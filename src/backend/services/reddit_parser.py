"""Reddit-specific content parser (PARSE-001).

Extracts structured post data from both new Reddit (shreddit-* custom
elements) and old Reddit (classic div/class layout). Falls back to empty
defaults when HTML does not match expected patterns.

Returns ``RedditPost`` which can be converted to ``ExtractedContent`` for
compatibility with the generic extraction pipeline.
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from contracts.extraction.extracted_content import ExtractedContent

log = logging.getLogger("buzzreach")

_MAX_COMMENTS = 10
_DELETED_MARKERS = {"[deleted]", "[removed]"}


@dataclass(frozen=True)
class RedditComment:
    """A single Reddit comment with metadata."""

    author: str
    score: int
    body: str


@dataclass(frozen=True)
class RedditPost:
    """Parsed Reddit post with structured metadata and top comments."""

    url: str
    title: str
    author: str
    score: int
    num_comments: int
    post_body: str
    top_comments: tuple[RedditComment, ...] = field(default_factory=tuple)

    def to_extracted_content(self) -> ExtractedContent:
        """Convert to ExtractedContent contract for pipeline compatibility."""
        comment_strings = [
            f"[{c.author} | {c.score} pts] {c.body}"
            for c in self.top_comments
        ]
        return ExtractedContent(
            url=self.url,
            title=self.title,
            body=self.post_body,
            comments=comment_strings,
            truncated=False,
        )


def is_reddit_url(url: str) -> bool:
    """Check if a URL belongs to reddit.com (www, old, or bare domain)."""
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    return host in {"reddit.com", "www.reddit.com", "old.reddit.com"}


def parse_reddit_post(html: str, url: str) -> RedditPost:
    """Parse Reddit HTML and extract post metadata and top comments.

    Tries new Reddit layout first, then falls back to old Reddit.
    Returns a RedditPost with empty defaults if neither layout matches.
    """
    cache_key = _make_cache_key(html, url)
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    soup = BeautifulSoup(html, "html.parser")

    result = _try_parse_new_reddit(soup, url)
    if result is None:
        result = _try_parse_old_reddit(soup, url)
    if result is None:
        log.info("Reddit parse miss", extra={"url": url})
        result = RedditPost(
            url=url, title="", author="", score=0,
            num_comments=0, post_body="",
        )

    _set_cached(cache_key, result)
    return result


def _try_parse_new_reddit(
    soup: BeautifulSoup, url: str
) -> RedditPost | None:
    """Parse new Reddit layout (shreddit-* custom elements)."""
    post_el = soup.find("shreddit-post")
    if post_el is None:
        return None

    title = post_el.get("post-title", "") or ""
    author = post_el.get("author", "") or ""
    score = _safe_int(post_el.get("score", "0"))
    num_comments = _safe_int(post_el.get("comment-count", "0"))
    post_body = _extract_md_text(post_el)

    comments = _parse_new_reddit_comments(soup)

    return RedditPost(
        url=url, title=title, author=author, score=score,
        num_comments=num_comments, post_body=post_body,
        top_comments=tuple(comments),
    )


def _parse_new_reddit_comments(
    soup: BeautifulSoup,
) -> list[RedditComment]:
    """Extract comments from shreddit-comment elements."""
    comments: list[RedditComment] = []
    for el in soup.find_all("shreddit-comment", limit=_MAX_COMMENTS):
        author = el.get("author", "") or ""
        score = _safe_int(el.get("score", "0"))
        body = _extract_md_text(el)

        if body in _DELETED_MARKERS:
            continue
        comments.append(RedditComment(author=author, score=score, body=body))

    return comments


def _try_parse_old_reddit(
    soup: BeautifulSoup, url: str
) -> RedditPost | None:
    """Parse old Reddit layout (classic div/class structure)."""
    link_el = soup.find("div", class_="thing")
    if link_el is None or "link" not in link_el.get("class", []):
        return None

    title = _old_reddit_title(link_el)
    author = _old_reddit_author(link_el)
    score = _old_reddit_score(link_el)
    post_body = _extract_md_text(link_el.find("div", class_="expando"))
    num_comments = _old_reddit_comment_count(soup)

    comments = _parse_old_reddit_comments(soup)

    return RedditPost(
        url=url, title=title, author=author, score=score,
        num_comments=num_comments, post_body=post_body,
        top_comments=tuple(comments),
    )


def _old_reddit_title(link_el: object) -> str:
    """Extract title from old Reddit link element."""
    title_el = link_el.find("a", class_="title")  # type: ignore[union-attr]
    return title_el.get_text(strip=True) if title_el else ""


def _old_reddit_author(link_el: object) -> str:
    """Extract author from old Reddit link element."""
    author_el = link_el.find("a", class_="author")  # type: ignore[union-attr]
    return author_el.get_text(strip=True) if author_el else ""


def _old_reddit_score(link_el: object) -> int:
    """Extract score from old Reddit link element."""
    score_el = link_el.find("div", class_="score")  # type: ignore[union-attr]
    if score_el:
        num_el = score_el.find("span", class_="number")
        if num_el:
            return _safe_int(num_el.get_text(strip=True))
    return 0


def _old_reddit_comment_count(soup: BeautifulSoup) -> int:
    """Extract comment count from old Reddit page."""
    comments_link = soup.find("a", class_="comments")
    if comments_link:
        text = comments_link.get_text(strip=True)
        match = re.search(r"(\d+)", text)
        if match:
            return int(match.group(1))
    return 0


def _parse_old_reddit_comments(
    soup: BeautifulSoup,
) -> list[RedditComment]:
    """Extract comments from old Reddit comment divs."""
    comments: list[RedditComment] = []
    comment_els = soup.find_all(
        "div", class_="comment", limit=_MAX_COMMENTS,
    )

    for el in comment_els:
        entry = el.find("div", class_="entry")
        if entry is None:
            continue

        author_el = entry.find("a", class_="author")
        author = author_el.get_text(strip=True) if author_el else ""

        score = _parse_old_comment_score(entry)
        body = _extract_md_text(entry.find("div", class_="md"))

        if body in _DELETED_MARKERS:
            continue
        comments.append(RedditComment(author=author, score=score, body=body))

    return comments


def _parse_old_comment_score(entry: object) -> int:
    """Parse score from old Reddit comment entry."""
    score_el = entry.find("span", class_="score")  # type: ignore[union-attr]
    if score_el:
        text = score_el.get_text(strip=True)
        match = re.search(r"(\d+)", text)
        if match:
            return int(match.group(1))
    return 0


def _extract_md_text(element: object) -> str:
    """Extract text from a .md content div, or return empty string."""
    if element is None:
        return ""
    md = element.find("div", class_="md")  # type: ignore[union-attr]
    target = md if md else element
    return target.get_text(separator="\n", strip=True)  # type: ignore[union-attr]


def _safe_int(value: str | None) -> int:
    """Parse an integer from a string, returning 0 on failure."""
    if not value:
        return 0
    try:
        return int(value.replace(",", ""))
    except (ValueError, AttributeError):
        return 0


# --- Cache (bounded LRU) ---

_CACHE: dict[str, RedditPost] = {}
_CACHE_MAX = 128


def _make_cache_key(html: str, url: str) -> str:
    """Create a cache key from URL + HTML content hash."""
    content_hash = hashlib.md5(  # noqa: S324
        html.encode("utf-8", errors="replace")
    ).hexdigest()
    return f"{url}:{content_hash}"


def _get_cached(key: str) -> RedditPost | None:
    """Retrieve a cached parse result."""
    return _CACHE.get(key)


def _set_cached(key: str, result: RedditPost) -> None:
    """Store a parse result in cache, evicting oldest if full."""
    if len(_CACHE) >= _CACHE_MAX:
        oldest_key = next(iter(_CACHE))
        del _CACHE[oldest_key]
    _CACHE[key] = result
