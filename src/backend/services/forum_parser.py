"""Forum thread parser (PARSE-003).

Extracts structured thread data from forum pages including title,
author, original post body, and reply chain. Falls back to empty
defaults when HTML does not match expected patterns.

Returns ``ForumThread`` which can be converted to ``ExtractedContent``
for compatibility with the generic extraction pipeline.
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from contracts.extraction.extracted_content import ExtractedContent

log = logging.getLogger("buzzreach")

_MAX_REPLIES = 10


@dataclass(frozen=True)
class ForumReply:
    """A single forum reply with metadata."""

    author: str
    text: str
    date: str


@dataclass(frozen=True)
class ForumThread:
    """Parsed forum thread with original post and replies."""

    url: str
    title: str
    author: str
    body: str
    replies: tuple[ForumReply, ...] = field(default_factory=tuple)

    def to_extracted_content(self) -> ExtractedContent:
        """Convert to ExtractedContent contract for pipeline compat."""
        comment_strings = [
            f"[{r.author}] {r.text}" for r in self.replies
        ]
        return ExtractedContent(
            url=self.url,
            title=self.title,
            body=self.body,
            comments=comment_strings,
            truncated=False,
        )


def parse_forum_thread(html: str, url: str) -> ForumThread:
    """Parse forum HTML and extract thread content plus replies.

    Detects common forum structures and extracts the original post
    and reply chain. Returns a ForumThread with empty defaults if
    nothing matches.
    """
    cache_key = _make_cache_key(html, url)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    soup = BeautifulSoup(html, "html.parser")

    title = _extract_title(soup)
    author = _extract_author(soup)
    body = _extract_body(soup)
    replies = _extract_replies(soup)

    result = ForumThread(
        url=url, title=title, author=author,
        body=body, replies=tuple(replies),
    )

    _cache_set(cache_key, result)
    return result


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract thread title from common forum HTML patterns."""
    selectors = [
        ".thread-title",
        ".topic-title",
        "h1.title",
        ".forum-thread h1",
        "h1",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)
    return ""


def _extract_author(soup: BeautifulSoup) -> str:
    """Extract thread author from common forum HTML patterns."""
    selectors = [
        ".thread-author a",
        ".thread-meta .author",
        ".topic-author a",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)

    meta = soup.select_one(".thread-meta, .thread-header .meta")
    if meta:
        text = meta.get_text(strip=True)
        match = re.search(r"(?:by|posted by)\s+(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _extract_body(soup: BeautifulSoup) -> str:
    """Extract original post body from common forum HTML patterns."""
    selectors = [
        ".thread-body",
        ".original-post",
        ".topic-body",
        ".forum-thread .post-body",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(separator="\n", strip=True)
    return ""


def _extract_replies(soup: BeautifulSoup) -> list[ForumReply]:
    """Extract reply posts from common forum HTML patterns."""
    replies: list[ForumReply] = []
    selectors = [
        ".forum-post.reply",
        ".reply-post",
        ".forum-replies .post",
    ]

    for sel in selectors:
        elements = soup.select(sel)
        if elements:
            for el in elements[:_MAX_REPLIES]:
                reply = _parse_single_reply(el)
                if reply is not None:
                    replies.append(reply)
            break

    return replies


def _parse_single_reply(el: object) -> ForumReply | None:
    """Parse a single forum reply element."""
    author_el = el.select_one(  # type: ignore[union-attr]
        ".post-author a, .reply-author a",
    )
    author = author_el.get_text(strip=True) if author_el else ""

    time_el = el.select_one(  # type: ignore[union-attr]
        "time.post-date, time.reply-date, time",
    )
    date = ""
    if time_el and time_el.get("datetime"):
        date = str(time_el["datetime"])
    elif time_el:
        date = time_el.get_text(strip=True)

    body_el = el.select_one(  # type: ignore[union-attr]
        ".post-body, .reply-body, .post-content",
    )
    text = body_el.get_text(separator=" ", strip=True) if body_el else ""

    if not text:
        return None
    return ForumReply(author=author, text=text, date=date)


# --- Cache (bounded LRU) ---

_CACHE: dict[str, ForumThread] = {}
_CACHE_MAX = 128


def _make_cache_key(html: str, url: str) -> str:
    """Create a cache key from URL + HTML content hash."""
    content_hash = hashlib.md5(  # noqa: S324
        html.encode("utf-8", errors="replace"),
    ).hexdigest()
    return f"{url}:{content_hash}"


def _cache_get(key: str) -> ForumThread | None:
    """Retrieve a cached parse result."""
    return _CACHE.get(key)


def _cache_set(key: str, result: ForumThread) -> None:
    """Store a parse result, evicting oldest if full."""
    if len(_CACHE) >= _CACHE_MAX:
        oldest_key = next(iter(_CACHE))
        del _CACHE[oldest_key]
    _CACHE[key] = result
