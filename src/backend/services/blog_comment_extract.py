"""Blog comment extraction helpers (PARSE-003).

Detects and extracts comments from WordPress native, Disqus, Medium
responses, and generic comment patterns. Used by blog_parser.py.
"""

import logging
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

log = logging.getLogger("buzzreach")

_MAX_COMMENTS = 10


@dataclass(frozen=True)
class RawComment:
    """A comment extracted from HTML before final processing."""

    author: str
    text: str
    date: str


def detect_comment_system(soup: BeautifulSoup) -> str:
    """Detect which comment system is used on the page.

    Returns one of: 'wordpress', 'disqus', 'medium', 'generic'.
    """
    if soup.find(id="disqus_thread") or soup.find(
        "script", string=re.compile(r"disqus", re.IGNORECASE),
    ):
        return "disqus"

    if soup.select_one(".comment-list .comment .comment-body"):
        return "wordpress"

    if soup.select_one("[data-testid='response']") or soup.select_one(
        "section.responses",
    ):
        return "medium"

    return "generic"


def extract_comments(
    soup: BeautifulSoup, system: str,
) -> list[RawComment]:
    """Extract comments using the appropriate strategy.

    Args:
        soup: Parsed HTML document.
        system: Comment system identifier from detect_comment_system.

    Returns:
        List of extracted comments, capped at _MAX_COMMENTS.
    """
    extractors = {
        "wordpress": _extract_wordpress_comments,
        "disqus": _extract_disqus_comments,
        "medium": _extract_medium_responses,
        "generic": _extract_generic_comments,
    }
    extractor = extractors.get(system, _extract_generic_comments)
    return extractor(soup)[:_MAX_COMMENTS]


def _extract_wordpress_comments(
    soup: BeautifulSoup,
) -> list[RawComment]:
    """Extract comments from WordPress native comment structure."""
    comments: list[RawComment] = []
    for el in soup.select(".comment .comment-body"):
        author = _wp_comment_author(el)
        date = _wp_comment_date(el)
        text = _wp_comment_text(el)
        if text:
            comments.append(RawComment(author=author, text=text, date=date))
    return comments


def _wp_comment_author(el: Tag) -> str:
    """Extract author from a WordPress comment-body element."""
    author_el = el.select_one(".comment-author .fn")
    if author_el:
        return author_el.get_text(strip=True)
    return ""


def _wp_comment_date(el: Tag) -> str:
    """Extract date from a WordPress comment-body element."""
    time_el = el.select_one("time.comment-date")
    if time_el and time_el.get("datetime"):
        return str(time_el["datetime"])
    if time_el:
        return time_el.get_text(strip=True)
    return ""


def _wp_comment_text(el: Tag) -> str:
    """Extract text from a WordPress comment-body element."""
    content_el = el.select_one(".comment-content")
    if content_el:
        return content_el.get_text(separator=" ", strip=True)
    return ""


def _extract_disqus_comments(
    soup: BeautifulSoup,
) -> list[RawComment]:
    """Extract comments from Disqus embedded comment elements."""
    comments: list[RawComment] = []
    for el in soup.select(".dsq-comment"):
        author = _dsq_author(el)
        date = _dsq_date(el)
        text = _dsq_text(el)
        if text:
            comments.append(RawComment(author=author, text=text, date=date))
    return comments


def _dsq_author(el: Tag) -> str:
    """Extract author from a Disqus comment element."""
    name_el = el.select_one(".dsq-commenter-name")
    if name_el:
        return name_el.get_text(strip=True)
    return ""


def _dsq_date(el: Tag) -> str:
    """Extract date from a Disqus comment element."""
    date_el = el.select_one(".dsq-comment-date")
    if date_el:
        return date_el.get_text(strip=True)
    return ""


def _dsq_text(el: Tag) -> str:
    """Extract text from a Disqus comment body element."""
    body_el = el.select_one(".dsq-comment-body")
    if body_el:
        return body_el.get_text(separator=" ", strip=True)
    return ""


def _extract_medium_responses(
    soup: BeautifulSoup,
) -> list[RawComment]:
    """Extract responses from Medium-style response section."""
    comments: list[RawComment] = []
    for el in soup.select("[data-testid='response'], .response"):
        author = _medium_author(el)
        date = _medium_date(el)
        text = _medium_text(el)
        if text:
            comments.append(RawComment(author=author, text=text, date=date))
    return comments


def _medium_author(el: Tag) -> str:
    """Extract author from a Medium response element."""
    author_el = el.select_one(".response-author")
    if author_el:
        return author_el.get_text(strip=True)
    return ""


def _medium_date(el: Tag) -> str:
    """Extract date from a Medium response element."""
    time_el = el.select_one("time")
    if time_el and time_el.get("datetime"):
        return str(time_el["datetime"])
    if time_el:
        return time_el.get_text(strip=True)
    return ""


def _medium_text(el: Tag) -> str:
    """Extract text from a Medium response element."""
    body_el = el.select_one(".response-body")
    if body_el:
        return body_el.get_text(separator=" ", strip=True)
    return ""


def _extract_generic_comments(
    soup: BeautifulSoup,
) -> list[RawComment]:
    """Extract comments using generic CSS selectors as fallback."""
    selectors = [
        ".comment",
        ".comments .comment",
        "[class*='comment']",
        ".reply",
        "[class*='reply']",
    ]
    seen: set[str] = set()
    comments: list[RawComment] = []

    for selector in selectors:
        for el in soup.select(selector):
            text = el.get_text(separator=" ", strip=True)
            if text and text not in seen:
                seen.add(text)
                comments.append(
                    RawComment(author="", text=text, date=""),
                )
    return comments


def extract_comment_count(soup: BeautifulSoup) -> int:
    """Extract the total comment count from common patterns.

    Looks for headings or elements containing "N comments" or
    "N responses" text patterns.
    """
    patterns = [
        re.compile(r"(\d+)\s*comments?", re.IGNORECASE),
        re.compile(r"(\d+)\s*responses?", re.IGNORECASE),
        re.compile(r"(\d+)\s*replies?", re.IGNORECASE),
    ]

    candidates = soup.select(
        ".comments-title, .comment-count, h2, h3, "
        "[class*='comment'] > h2, [class*='comment'] > h3",
    )
    for el in candidates:
        text = el.get_text(strip=True)
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return int(match.group(1))

    return 0
