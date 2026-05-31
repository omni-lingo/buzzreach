"""Blog comment parser (PARSE-003).

Extracts structured post data from blog platforms (WordPress, Medium,
Disqus-powered sites). Falls back to empty defaults when HTML does not
match expected patterns.

Returns ``BlogPost`` which can be converted to ``ExtractedContent`` for
compatibility with the generic extraction pipeline.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from contracts.extraction.extracted_content import ExtractedContent
from src.backend.services.blog_comment_extract import (
    RawComment,
    detect_comment_system,
    extract_comment_count,
    extract_comments,
)
from src.backend.services.forum_parser import (
    ForumReply,
    ForumThread,
    parse_forum_thread,
)

log = logging.getLogger("buzzreach")

_BLOG_DOMAINS = frozenset({
    "medium.com",
    "dev.to",
    "hashnode.dev",
    "substack.com",
    "wordpress.com",
})

__all__ = [
    "BlogComment",
    "BlogPost",
    "ForumReply",
    "ForumThread",
    "is_blog_url",
    "parse_blog_post",
    "parse_forum_thread",
]


@dataclass(frozen=True)
class BlogComment:
    """A single blog comment with metadata."""

    author: str
    text: str
    date: str


@dataclass(frozen=True)
class BlogPost:
    """Parsed blog post with article content and comments."""

    url: str
    title: str
    author: str
    pub_date: str
    body: str
    comment_count: int
    comments: tuple[BlogComment, ...] = field(default_factory=tuple)

    def to_extracted_content(self) -> ExtractedContent:
        """Convert to ExtractedContent contract for pipeline compat."""
        comment_strings = [
            f"[{c.author}] {c.text}" for c in self.comments
        ]
        return ExtractedContent(
            url=self.url,
            title=self.title,
            body=self.body,
            comments=comment_strings,
            truncated=False,
        )


def is_blog_url(url: str) -> bool:
    """Check if a URL belongs to a known blog platform."""
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    return any(
        host == domain or host.endswith(f".{domain}")
        for domain in _BLOG_DOMAINS
    )


def parse_blog_post(html: str, url: str) -> BlogPost:
    """Parse blog HTML and extract post content plus comments.

    Detects the comment system (WordPress, Disqus, Medium, generic)
    and uses the appropriate extractor. Returns a BlogPost with empty
    defaults if the page does not match expected patterns.
    """
    cache_key = _make_cache_key(html, url)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    soup = BeautifulSoup(html, "html.parser")

    title = _extract_title(soup)
    author = _extract_author(soup)
    pub_date = _extract_pub_date(soup)
    body = _extract_body(soup)

    system = detect_comment_system(soup)
    raw_comments = extract_comments(soup, system)
    comment_count = extract_comment_count(soup)
    if comment_count == 0:
        comment_count = len(raw_comments)

    comments = tuple(
        _raw_to_blog_comment(rc) for rc in raw_comments
    )

    result = BlogPost(
        url=url, title=title, author=author, pub_date=pub_date,
        body=body, comment_count=comment_count, comments=comments,
    )

    _cache_set(cache_key, result)
    return result


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract post title from common blog HTML patterns."""
    selectors = [
        "h1.entry-title", "h1.post-title",
        "article h1", "header h1", "h1",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)
    return ""


def _extract_author(soup: BeautifulSoup) -> str:
    """Extract author name from common blog HTML patterns."""
    selectors = [
        ".author.vcard .fn", ".author-name",
        ".post-meta .author a", "[rel='author']", ".author a",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)
    return ""


def _extract_pub_date(soup: BeautifulSoup) -> str:
    """Extract publication date from common blog HTML patterns."""
    time_el = soup.select_one(
        "time.entry-date, time.published, "
        "article time[datetime], header time[datetime]",
    )
    if time_el and time_el.get("datetime"):
        return str(time_el["datetime"])
    if time_el:
        return time_el.get_text(strip=True)
    return ""


def _extract_body(soup: BeautifulSoup) -> str:
    """Extract article body text from common blog HTML patterns."""
    selectors = [
        ".entry-content", ".post-content",
        ".article-body", "article .content", "article section",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(separator="\n", strip=True)
    return ""


def _raw_to_blog_comment(raw: RawComment) -> BlogComment:
    """Convert a RawComment to a BlogComment."""
    return BlogComment(author=raw.author, text=raw.text, date=raw.date)


# --- Cache (bounded LRU) ---

_CACHE: dict[str, BlogPost] = {}
_CACHE_MAX = 128


def _make_cache_key(html: str, url: str) -> str:
    """Create a cache key from URL + HTML content hash."""
    content_hash = hashlib.md5(  # noqa: S324
        html.encode("utf-8", errors="replace"),
    ).hexdigest()
    return f"{url}:{content_hash}"


def _cache_get(key: str) -> BlogPost | None:
    """Retrieve a cached blog parse result."""
    return _CACHE.get(key)


def _cache_set(key: str, result: BlogPost) -> None:
    """Store a blog parse result, evicting oldest if full."""
    if len(_CACHE) >= _CACHE_MAX:
        oldest_key = next(iter(_CACHE))
        del _CACHE[oldest_key]
    _CACHE[key] = result
