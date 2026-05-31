"""Content extractor (EXT-001).

Fetches a page via httpx, runs readability + BeautifulSoup to pull the
main body and visible comment text. Site-specific parsers (Reddit,
Quora, blog) are tried before falling back to the generic pipeline.

Raises ``AppError(code="EXTRACTION_FAILED")`` on unrecoverable errors.
"""

import logging

import httpx
from bs4 import BeautifulSoup
from readability import Document

from contracts.extraction.extracted_content import ExtractedContent
from src.backend.errors import AppError
from src.backend.services.blog_parser import is_blog_url, parse_blog_post
from src.backend.services.quora_parser import is_quora_url, parse_quora_question
from src.backend.services.reddit_parser import is_reddit_url, parse_reddit_post
from src.backend.settings import Settings

log = logging.getLogger("buzzreach")

_COMMENT_SELECTORS = [
    ".comment",
    ".comments .comment",
    "[class*='comment']",
    ".reply",
    "[class*='reply']",
]


def extract(
    url: str,
    settings: Settings,
    *,
    transport: httpx.BaseTransport | None = None,
) -> ExtractedContent:
    """Fetch a page and extract its main body and comments.

    Args:
        url: URL to fetch and extract.
        settings: Application settings with timeout and char budget.
        transport: Optional httpx transport override for testing.

    Returns:
        ExtractedContent with body, comments, and truncation flag.

    Raises:
        AppError: ``EXTRACTION_FAILED`` on fetch or parse failure.
    """
    html = _fetch_html(url, settings, transport)

    if is_reddit_url(url):
        result = _try_reddit_parser(html, url, settings)
        if result is not None:
            return result

    if is_quora_url(url):
        result = _try_quora_parser(html, url, settings)
        if result is not None:
            return result

    if is_blog_url(url):
        result = _try_blog_parser(html, url, settings)
        if result is not None:
            return result

    title, body = _extract_body(html, url)
    comments = _extract_comments(html)
    return _apply_char_budget(
        url=url,
        title=title,
        body=body,
        comments=comments,
        budget=settings.extraction_char_budget,
    )


def _try_reddit_parser(
    html: str, url: str, settings: Settings
) -> ExtractedContent | None:
    """Attempt Reddit-specific parsing; return None to fall back to generic."""
    try:
        post = parse_reddit_post(html, url)
        if not post.title and not post.post_body:
            return None
        content = post.to_extracted_content()
        return _apply_char_budget(
            url=content.url,
            title=content.title,
            body=content.body,
            comments=content.comments,
            budget=settings.extraction_char_budget,
        )
    except Exception:
        log.info("Reddit parser fallback", extra={"url": url})
        return None


def _try_quora_parser(
    html: str, url: str, settings: Settings,
) -> ExtractedContent | None:
    """Attempt Quora-specific parsing; return None to fall back to generic."""
    try:
        question = parse_quora_question(html, url)
        if not question.title and not question.answers:
            return None
        content = question.to_extracted_content()
        return _apply_char_budget(
            url=content.url,
            title=content.title,
            body=content.body,
            comments=content.comments,
            budget=settings.extraction_char_budget,
        )
    except Exception:
        log.info("Quora parser fallback", extra={"url": url})
        return None


def _try_blog_parser(
    html: str, url: str, settings: Settings,
) -> ExtractedContent | None:
    """Attempt blog-specific parsing; return None to fall back to generic."""
    try:
        post = parse_blog_post(html, url)
        if not post.title and not post.body:
            return None
        content = post.to_extracted_content()
        return _apply_char_budget(
            url=content.url,
            title=content.title,
            body=content.body,
            comments=content.comments,
            budget=settings.extraction_char_budget,
        )
    except Exception:
        log.info("Blog parser fallback", extra={"url": url})
        return None


def _fetch_html(
    url: str,
    settings: Settings,
    transport: httpx.BaseTransport | None,
) -> str:
    """Fetch the raw HTML from the URL."""
    try:
        client_kwargs: dict[str, object] = {
            "timeout": settings.extraction_timeout_seconds,
            "follow_redirects": True,
        }
        if transport is not None:
            client_kwargs["transport"] = transport

        with httpx.Client(**client_kwargs) as client:
            response = client.get(url)

        if response.status_code >= 400:
            log.warning(
                "Extraction fetch failed",
                extra={"url": url, "status": response.status_code},
            )
            raise AppError(
                code="EXTRACTION_FAILED",
                message=f"HTTP {response.status_code} fetching {url}",
            )

        return response.text

    except AppError:
        raise
    except Exception as exc:
        log.warning(
            "Extraction fetch error",
            extra={"url": url, "error": str(exc)},
        )
        raise AppError(
            code="EXTRACTION_FAILED",
            message=f"Failed to fetch {url}: {exc}",
        ) from exc


def _extract_body(html: str, url: str) -> tuple[str, str]:
    """Extract the main article title and body text via Readability.

    Returns:
        Tuple of (title, body_text).

    Raises:
        AppError: ``EXTRACTION_FAILED`` if the page has no extractable
            content.
    """
    try:
        doc = Document(html, url=url)
        title = doc.short_title() or ""
        summary_html = doc.summary()
    except Exception as exc:
        log.warning(
            "Readability parse error",
            extra={"url": url, "error": str(exc)},
        )
        raise AppError(
            code="EXTRACTION_FAILED",
            message=f"Failed to parse content from {url}",
        ) from exc

    soup = BeautifulSoup(summary_html, "html.parser")
    body_text = soup.get_text(separator="\n", strip=True)

    if not body_text.strip():
        raise AppError(
            code="EXTRACTION_FAILED",
            message=f"No extractable content from {url}",
        )

    return title, body_text


def _extract_comments(html: str) -> list[str]:
    """Extract visible comment text from the raw HTML.

    Uses common CSS selectors for comment-like elements. Returns a list
    of non-empty comment strings.
    """
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    comments: list[str] = []

    for selector in _COMMENT_SELECTORS:
        for element in soup.select(selector):
            text = element.get_text(separator=" ", strip=True)
            if text and text not in seen:
                seen.add(text)
                comments.append(text)

    return comments


def _apply_char_budget(
    url: str,
    title: str,
    body: str,
    comments: list[str],
    budget: int,
) -> ExtractedContent:
    """Truncate body + comments to fit within the char budget.

    Body is prioritised: it gets truncated first to its share, then
    remaining budget goes to comments.
    """
    total = len(body) + sum(len(c) for c in comments)

    if total <= budget:
        return ExtractedContent(
            url=url,
            title=title,
            body=body,
            comments=comments,
            truncated=False,
        )

    # Reserve 80% of budget for body, 20% for comments
    body_budget = int(budget * 0.8)
    comment_budget = budget - body_budget

    truncated_body = body[:body_budget]
    truncated_comments = _truncate_comments(comments, comment_budget)

    return ExtractedContent(
        url=url,
        title=title,
        body=truncated_body,
        comments=truncated_comments,
        truncated=True,
    )


def _truncate_comments(
    comments: list[str], budget: int
) -> list[str]:
    """Keep as many full comments as fit within the budget."""
    result: list[str] = []
    remaining = budget

    for comment in comments:
        if remaining <= 0:
            break
        if len(comment) <= remaining:
            result.append(comment)
            remaining -= len(comment)
        else:
            result.append(comment[:remaining])
            remaining = 0

    return result
