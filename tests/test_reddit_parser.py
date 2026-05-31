"""Tests for the Reddit-specific content parser (PARSE-001).

Uses saved HTML fixtures for new Reddit, old Reddit, and deleted post
layouts. Parser operates on raw HTML strings — no HTTP involved.
"""

from pathlib import Path

from contracts.extraction.extracted_content import ExtractedContent
from src.backend.services.reddit_parser import (
    RedditComment,
    is_reddit_url,
    parse_reddit_post,
)

_FIXTURE_DIR = Path(__file__).parent / "fixtures"
_NEW_HTML = (_FIXTURE_DIR / "reddit_new.html").read_text(encoding="utf-8")
_OLD_HTML = (_FIXTURE_DIR / "reddit_old.html").read_text(encoding="utf-8")
_DELETED_HTML = (_FIXTURE_DIR / "reddit_deleted.html").read_text(encoding="utf-8")

_NEW_URL = "https://www.reddit.com/r/personalfinance/comments/abc123/best_tax_software/"
_OLD_URL = "https://old.reddit.com/r/personalfinance/comments/abc123/best_tax_software/"


class TestIsRedditUrl:
    """URL detection for reddit.com domains."""

    def test_www_reddit_com(self) -> None:
        assert is_reddit_url("https://www.reddit.com/r/test/comments/abc/title/") is True

    def test_reddit_com(self) -> None:
        assert is_reddit_url("https://reddit.com/r/test/comments/abc/title/") is True

    def test_old_reddit(self) -> None:
        assert is_reddit_url("https://old.reddit.com/r/test/comments/abc/title/") is True

    def test_non_reddit(self) -> None:
        assert is_reddit_url("https://stackoverflow.com/questions/123") is False

    def test_reddit_in_path(self) -> None:
        assert is_reddit_url("https://example.com/reddit.com/fake") is False


class TestNewRedditParsing:
    """Parsing new Reddit (shreddit-* custom elements)."""

    def test_extracts_title(self) -> None:
        result = parse_reddit_post(_NEW_HTML, _NEW_URL)
        assert result.title == "Best tax software for 2024?"

    def test_extracts_author(self) -> None:
        result = parse_reddit_post(_NEW_HTML, _NEW_URL)
        assert result.author == "taxpayer_2024"

    def test_extracts_score(self) -> None:
        result = parse_reddit_post(_NEW_HTML, _NEW_URL)
        assert result.score == 142

    def test_extracts_comment_count(self) -> None:
        result = parse_reddit_post(_NEW_HTML, _NEW_URL)
        assert result.num_comments == 37

    def test_extracts_post_body(self) -> None:
        result = parse_reddit_post(_NEW_HTML, _NEW_URL)
        assert "TurboTax" in result.post_body
        assert "W-2" in result.post_body

    def test_extracts_top_comments(self) -> None:
        result = parse_reddit_post(_NEW_HTML, _NEW_URL)
        assert len(result.top_comments) >= 5
        first = result.top_comments[0]
        assert first.author == "finance_guru"
        assert first.score == 89
        assert "FreeTaxUSA" in first.body

    def test_comment_is_reddit_comment_type(self) -> None:
        result = parse_reddit_post(_NEW_HTML, _NEW_URL)
        assert all(isinstance(c, RedditComment) for c in result.top_comments)

    def test_limits_top_comments_to_ten(self) -> None:
        result = parse_reddit_post(_NEW_HTML, _NEW_URL)
        assert len(result.top_comments) <= 10


class TestOldRedditParsing:
    """Parsing old.reddit.com layout (classic divs + classes)."""

    def test_extracts_title(self) -> None:
        result = parse_reddit_post(_OLD_HTML, _OLD_URL)
        assert result.title == "Best tax software for 2024?"

    def test_extracts_author(self) -> None:
        result = parse_reddit_post(_OLD_HTML, _OLD_URL)
        assert result.author == "taxpayer_2024"

    def test_extracts_score(self) -> None:
        result = parse_reddit_post(_OLD_HTML, _OLD_URL)
        assert result.score == 142

    def test_extracts_post_body(self) -> None:
        result = parse_reddit_post(_OLD_HTML, _OLD_URL)
        assert "TurboTax" in result.post_body

    def test_extracts_comments(self) -> None:
        result = parse_reddit_post(_OLD_HTML, _OLD_URL)
        assert len(result.top_comments) >= 3
        authors = [c.author for c in result.top_comments]
        assert "finance_guru" in authors

    def test_comment_scores_extracted(self) -> None:
        result = parse_reddit_post(_OLD_HTML, _OLD_URL)
        guru = next(c for c in result.top_comments if c.author == "finance_guru")
        assert guru.score == 89


class TestDeletedPost:
    """Graceful handling of deleted/removed posts."""

    def test_handles_deleted_author(self) -> None:
        result = parse_reddit_post(_DELETED_HTML, _NEW_URL)
        assert result.author == "[deleted]"

    def test_handles_removed_body(self) -> None:
        result = parse_reddit_post(_DELETED_HTML, _NEW_URL)
        assert result.post_body == "[removed]"

    def test_filters_deleted_comments(self) -> None:
        result = parse_reddit_post(_DELETED_HTML, _NEW_URL)
        bodies = [c.body for c in result.top_comments]
        assert "[deleted]" not in bodies

    def test_keeps_valid_comments(self) -> None:
        result = parse_reddit_post(_DELETED_HTML, _NEW_URL)
        assert len(result.top_comments) >= 1
        assert result.top_comments[0].author == "helpful_user"


class TestToExtractedContent:
    """RedditPost converts to ExtractedContent contract."""

    def test_converts_to_extracted_content(self) -> None:
        result = parse_reddit_post(_NEW_HTML, _NEW_URL)
        content = result.to_extracted_content()

        assert isinstance(content, ExtractedContent)
        assert content.url == _NEW_URL
        assert "Best tax software" in content.title
        assert "TurboTax" in content.body
        assert len(content.comments) >= 1

    def test_comments_include_author_and_score(self) -> None:
        result = parse_reddit_post(_NEW_HTML, _NEW_URL)
        content = result.to_extracted_content()

        first_comment = content.comments[0]
        assert "finance_guru" in first_comment
        assert "89" in first_comment


class TestFallbackToGenericExtractor:
    """Falls back to generic extractor on parsing errors."""

    def test_fallback_on_non_reddit_html(self) -> None:
        html = "<html><body><p>Just a normal page</p></body></html>"
        result = parse_reddit_post(html, _NEW_URL)
        assert result.title == ""
        assert result.score == 0
        assert result.num_comments == 0

    def test_fallback_on_empty_html(self) -> None:
        result = parse_reddit_post("", _NEW_URL)
        assert result.title == ""
        assert result.score == 0


class TestCaching:
    """Same URL + HTML returns cached result."""

    def test_same_input_returns_cached_result(self) -> None:
        result1 = parse_reddit_post(_NEW_HTML, _NEW_URL)
        result2 = parse_reddit_post(_NEW_HTML, _NEW_URL)
        assert result1 == result2

    def test_different_url_returns_different_result(self) -> None:
        result1 = parse_reddit_post(_NEW_HTML, _NEW_URL)
        result2 = parse_reddit_post(_OLD_HTML, _OLD_URL)
        assert result1 != result2
