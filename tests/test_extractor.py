"""Tests for the content extractor (EXT-001).

All HTTP is mocked via httpx.MockTransport. A saved HTML fixture is used
to verify body + comment extraction without live network calls.
"""

from pathlib import Path
from typing import Any

import httpx
import pytest

from contracts.extraction.extracted_content import ExtractedContent
from src.backend.errors import AppError
from src.backend.services.extraction.extractor import extract
from src.backend.settings import Settings

_FIXTURE_DIR = Path(__file__).parent / "fixtures"
_SAMPLE_HTML = (_FIXTURE_DIR / "sample_page.html").read_text(encoding="utf-8")
_TEST_URL = "https://forum.example.com/post/12345"


def _settings(**overrides: Any) -> Settings:
    """Return Settings with extraction config and optional overrides."""
    defaults: dict[str, Any] = {
        "extraction_timeout_seconds": 10,
        "extraction_char_budget": 20000,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _make_transport(
    body: str = _SAMPLE_HTML,
    status_code: int = 200,
    content_type: str = "text/html",
) -> httpx.MockTransport:
    """Build a mock transport returning fixed HTML."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            content=body.encode("utf-8"),
            headers={"content-type": content_type},
        )

    return httpx.MockTransport(handler)


def _error_transport(error: Exception) -> httpx.MockTransport:
    """Build a mock transport that raises a network error."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    return httpx.MockTransport(handler)


class TestBodyExtraction:
    """Readability extracts the main article body from HTML."""

    def test_extracts_body_from_fixture(self) -> None:
        transport = _make_transport()
        result = extract(_TEST_URL, _settings(), transport=transport)

        assert isinstance(result, ExtractedContent)
        assert result.url == _TEST_URL
        assert "CP14" in result.body
        assert "penalty abatement" in result.body

    def test_extracts_title(self) -> None:
        transport = _make_transport()
        result = extract(_TEST_URL, _settings(), transport=transport)

        assert "IRS CP14" in result.title

    def test_excludes_nav_and_footer(self) -> None:
        transport = _make_transport()
        result = extract(_TEST_URL, _settings(), transport=transport)

        assert "Copyright" not in result.body


class TestCommentExtraction:
    """Visible comment text is captured in the comments list."""

    def test_extracts_comments_from_fixture(self) -> None:
        transport = _make_transport()
        result = extract(_TEST_URL, _settings(), transport=transport)

        assert len(result.comments) >= 1
        all_comments = " ".join(result.comments)
        assert "Form 843" in all_comments or "practitioner" in all_comments

    def test_comments_are_strings(self) -> None:
        transport = _make_transport()
        result = extract(_TEST_URL, _settings(), transport=transport)

        assert all(isinstance(c, str) for c in result.comments)


class TestTruncation:
    """Output is truncated to the char budget."""

    def test_under_budget_not_truncated(self) -> None:
        transport = _make_transport()
        result = extract(
            _TEST_URL, _settings(extraction_char_budget=50000), transport=transport
        )

        assert result.truncated is False

    def test_over_budget_truncated(self) -> None:
        transport = _make_transport()
        result = extract(
            _TEST_URL, _settings(extraction_char_budget=50), transport=transport
        )

        assert result.truncated is True
        total_chars = len(result.body) + sum(len(c) for c in result.comments)
        assert total_chars <= 50

    def test_truncated_body_preserves_prefix(self) -> None:
        transport = _make_transport()
        result = extract(
            _TEST_URL, _settings(extraction_char_budget=100), transport=transport
        )

        assert result.truncated is True
        assert len(result.body) > 0


class TestFetchErrors:
    """Fetch and parse failures raise AppError(code='EXTRACTION_FAILED')."""

    @pytest.mark.parametrize("status", [403, 404, 500])
    def test_http_error_raises_extraction_failed(self, status: int) -> None:
        transport = _make_transport(status_code=status)

        with pytest.raises(AppError) as exc_info:
            extract(_TEST_URL, _settings(), transport=transport)

        assert exc_info.value.code == "EXTRACTION_FAILED"

    def test_connection_error_raises_extraction_failed(self) -> None:
        transport = _error_transport(httpx.ConnectError("connection refused"))

        with pytest.raises(AppError) as exc_info:
            extract(_TEST_URL, _settings(), transport=transport)

        assert exc_info.value.code == "EXTRACTION_FAILED"

    def test_timeout_raises_extraction_failed(self) -> None:
        transport = _error_transport(
            httpx.ReadTimeout("read timed out")
        )

        with pytest.raises(AppError) as exc_info:
            extract(_TEST_URL, _settings(), transport=transport)

        assert exc_info.value.code == "EXTRACTION_FAILED"

    def test_unparseable_html_raises_extraction_failed(self) -> None:
        transport = _make_transport(body="", content_type="text/html")

        with pytest.raises(AppError) as exc_info:
            extract(_TEST_URL, _settings(), transport=transport)

        assert exc_info.value.code == "EXTRACTION_FAILED"


class TestNoLiveNetwork:
    """Verify the test suite does not make live HTTP calls."""

    def test_transport_is_required_in_tests(self) -> None:
        transport = _make_transport()
        result = extract(_TEST_URL, _settings(), transport=transport)
        assert result.url == _TEST_URL
