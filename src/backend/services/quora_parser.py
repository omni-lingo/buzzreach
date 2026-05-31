"""Quora-specific content parser (PARSE-002).

Extracts structured question data from Quora pages including question title,
author, follower count, and answers with upvotes. Falls back to empty defaults
when HTML does not match expected patterns.

Returns ``QuoraQuestion`` which can be converted to ``ExtractedContent`` for
compatibility with the generic extraction pipeline.
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from contracts.extraction.extracted_content import ExtractedContent

log = logging.getLogger("buzzreach")

_MAX_ANSWERS = 10
_DELETED_MARKERS = frozenset({
    "this question has been deleted",
    "no longer available",
    "question has been removed",
})


@dataclass(frozen=True)
class QuoraAnswer:
    """A single Quora answer with metadata."""

    author: str
    upvotes: int
    text: str
    truncated: bool = False


@dataclass(frozen=True)
class QuoraQuestion:
    """Parsed Quora question with answers and metadata."""

    url: str
    title: str
    author: str
    followers_count: int
    answers: tuple[QuoraAnswer, ...] = field(default_factory=tuple)

    def to_extracted_content(self) -> ExtractedContent:
        """Convert to ExtractedContent contract for pipeline compat."""
        body = self.answers[0].text if self.answers else ""
        remaining = self.answers[1:] if len(self.answers) > 1 else ()
        comment_strings = [
            f"[{a.author} | {a.upvotes} upvotes] {a.text}"
            for a in remaining
        ]
        return ExtractedContent(
            url=self.url,
            title=self.title,
            body=body,
            comments=comment_strings,
            truncated=False,
        )


def is_quora_url(url: str) -> bool:
    """Check if a URL belongs to quora.com (www, bare, or locale subdomains)."""
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    return host == "quora.com" or host.endswith(".quora.com")


def parse_quora_question(html: str, url: str) -> QuoraQuestion:
    """Parse Quora HTML and extract question + answers.

    Tries data-testid selectors first, then falls back to class-based
    selectors. Returns a QuoraQuestion with empty defaults if nothing
    matches.
    """
    cache_key = _make_cache_key(html, url)
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    soup = BeautifulSoup(html, "html.parser")

    if _is_deleted_question(soup):
        result = QuoraQuestion(
            url=url, title="", author="", followers_count=0,
        )
        _set_cached(cache_key, result)
        return result

    title = _extract_title(soup)
    author = _extract_author(soup)
    followers_count = _extract_followers_count(soup)
    answers = _extract_answers(soup)

    result = QuoraQuestion(
        url=url,
        title=title,
        author=author,
        followers_count=followers_count,
        answers=tuple(answers),
    )

    _set_cached(cache_key, result)
    return result


def _is_deleted_question(soup: BeautifulSoup) -> bool:
    """Detect deleted or unavailable Quora questions."""
    deleted_el = soup.find(attrs={"data-testid": "deleted_question"})
    if deleted_el:
        return True
    page_text = soup.get_text(separator=" ", strip=True).lower()
    return any(marker in page_text for marker in _DELETED_MARKERS)


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract the question title from Quora HTML."""
    title_el = soup.find(
        "div", class_=lambda c: c and "dynamicFontSize--xxlarge" in c,
    )
    if title_el:
        span = title_el.find("span", recursive=True)
        if span:
            return _deep_text(span)
    return ""


def _extract_author(soup: BeautifulSoup) -> str:
    """Extract the question asker's name."""
    asker_el = soup.find(attrs={"data-testid": "question_asker"})
    if asker_el:
        link = asker_el.find("a")
        if link:
            return link.get_text(strip=True)
    return ""


def _extract_followers_count(soup: BeautifulSoup) -> int:
    """Extract the question follower count."""
    follower_el = soup.find(
        attrs={"data-testid": "question_follower_count"},
    )
    if follower_el:
        text = follower_el.get_text(strip=True)
        return _parse_count(text)
    return 0


def _extract_answers(soup: BeautifulSoup) -> list[QuoraAnswer]:
    """Extract answers from the answers container."""
    answers: list[QuoraAnswer] = []
    answer_els = soup.find_all(
        attrs={"data-testid": "answer"}, limit=_MAX_ANSWERS,
    )

    for el in answer_els:
        answer = _parse_single_answer(el)
        if answer is not None:
            answers.append(answer)

    return answers


def _parse_single_answer(el: Tag) -> QuoraAnswer | None:
    """Parse a single answer element into a QuoraAnswer."""
    author = _answer_author(el)
    upvotes = _answer_upvotes(el)
    text = _answer_text(el)
    truncated = _is_answer_truncated(el)

    if not text:
        return None

    return QuoraAnswer(
        author=author, upvotes=upvotes, text=text, truncated=truncated,
    )


def _answer_author(el: Tag) -> str:
    """Extract author name from an answer element."""
    author_el = el.find(attrs={"data-testid": "answer_author"})
    if author_el:
        link = author_el.find("a")
        if link:
            return link.get_text(strip=True)
    return ""


def _answer_upvotes(el: Tag) -> int:
    """Extract upvote count from an answer element."""
    upvote_el = el.find(attrs={"data-testid": "answer_upvote_count"})
    if upvote_el:
        text = upvote_el.get_text(strip=True)
        return _parse_count(text)
    return 0


def _answer_text(el: Tag) -> str:
    """Extract the answer body text."""
    content_el = el.find(attrs={"data-testid": "answer_content"})
    if content_el is None:
        return ""
    clone = BeautifulSoup(str(content_el), "html.parser")
    for trunc in clone.find_all(
        attrs={"data-testid": "truncated_content"},
    ):
        trunc.decompose()
    return clone.get_text(separator="\n", strip=True)


def _is_answer_truncated(el: Tag) -> bool:
    """Check if the answer has truncated/collapsed content."""
    content_el = el.find(attrs={"data-testid": "answer_content"})
    if content_el is None:
        return False
    trunc = content_el.find(attrs={"data-testid": "truncated_content"})
    if trunc:
        return True
    collapsed = el.get("data-collapsed")
    return collapsed == "true"


def _deep_text(element: Tag) -> str:
    """Get the deepest text content from nested spans."""
    spans = element.find_all("span", recursive=True)
    if spans:
        return spans[-1].get_text(strip=True)
    return element.get_text(strip=True)


def _parse_count(text: str) -> int:
    """Parse a numeric count from text like '1,234 followers'."""
    match = re.search(r"([\d,]+)", text)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0


# --- Cache (bounded LRU) ---

_CACHE: dict[str, QuoraQuestion] = {}
_CACHE_MAX = 128


def _make_cache_key(html: str, url: str) -> str:
    """Create a cache key from URL + HTML content hash."""
    content_hash = hashlib.md5(  # noqa: S324
        html.encode("utf-8", errors="replace"),
    ).hexdigest()
    return f"{url}:{content_hash}"


def _get_cached(key: str) -> QuoraQuestion | None:
    """Retrieve a cached parse result."""
    return _CACHE.get(key)


def _set_cached(key: str, result: QuoraQuestion) -> None:
    """Store a parse result in cache, evicting oldest if full."""
    if len(_CACHE) >= _CACHE_MAX:
        oldest_key = next(iter(_CACHE))
        del _CACHE[oldest_key]
    _CACHE[key] = result
