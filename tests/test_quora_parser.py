"""Tests for the Quora-specific content parser (PARSE-002).

Uses saved HTML fixtures for standard questions, deleted questions, and
collapsed answers. Parser operates on raw HTML strings — no HTTP involved.
"""

from pathlib import Path

from contracts.extraction.extracted_content import ExtractedContent
from src.backend.services.quora_parser import (
    QuoraAnswer,
    is_quora_url,
    parse_quora_question,
)

_FIXTURE_DIR = Path(__file__).parent / "fixtures"
_QUESTION_HTML = (_FIXTURE_DIR / "quora_question.html").read_text(encoding="utf-8")
_DELETED_HTML = (_FIXTURE_DIR / "quora_deleted.html").read_text(encoding="utf-8")
_COLLAPSED_HTML = (_FIXTURE_DIR / "quora_collapsed.html").read_text(encoding="utf-8")

_QUESTION_URL = "https://www.quora.com/What-is-the-best-programming-language-for-beginners"
_DELETED_URL = "https://www.quora.com/Some-deleted-question"
_COLLAPSED_URL = "https://www.quora.com/How-do-you-stay-productive-working-from-home"


class TestIsQuoraUrl:
    """URL detection for quora.com domains."""

    def test_www_quora_com(self) -> None:
        assert is_quora_url("https://www.quora.com/Some-question") is True

    def test_quora_com(self) -> None:
        assert is_quora_url("https://quora.com/Some-question") is True

    def test_subdomain_quora(self) -> None:
        assert is_quora_url("https://fr.quora.com/Some-question") is True

    def test_non_quora(self) -> None:
        assert is_quora_url("https://stackoverflow.com/questions/123") is False

    def test_quora_in_path(self) -> None:
        assert is_quora_url("https://example.com/quora.com/fake") is False

    def test_invalid_url(self) -> None:
        assert is_quora_url("not a url") is False


class TestQuoraQuestionParsing:
    """Parsing standard Quora question pages."""

    def test_extracts_title(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        assert result.title == "What is the best programming language for beginners?"

    def test_extracts_author(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        assert result.author == "Jane Developer"

    def test_extracts_followers_count(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        assert result.followers_count == 1234

    def test_extracts_answers(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        assert len(result.answers) == 4

    def test_first_answer_author(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        assert result.answers[0].author == "John Coder"

    def test_first_answer_upvotes(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        assert result.answers[0].upvotes == 2345

    def test_first_answer_text(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        assert "Python" in result.answers[0].text
        assert "beginners" in result.answers[0].text

    def test_answer_is_quora_answer_type(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        assert all(isinstance(a, QuoraAnswer) for a in result.answers)

    def test_answers_sorted_by_upvotes(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        upvotes = [a.upvotes for a in result.answers]
        assert upvotes == sorted(upvotes, reverse=True)


class TestDeletedQuestion:
    """Graceful handling of deleted/unavailable questions."""

    def test_handles_deleted_question(self) -> None:
        result = parse_quora_question(_DELETED_HTML, _DELETED_URL)
        assert result.title == ""
        assert result.author == ""
        assert result.answers == ()

    def test_deleted_has_zero_followers(self) -> None:
        result = parse_quora_question(_DELETED_HTML, _DELETED_URL)
        assert result.followers_count == 0


class TestCollapsedAnswers:
    """Handles collapsed/truncated answers gracefully."""

    def test_extracts_visible_text_from_collapsed(self) -> None:
        result = parse_quora_question(_COLLAPSED_HTML, _COLLAPSED_URL)
        assert len(result.answers) >= 1
        first = result.answers[0]
        assert "dedicated workspace" in first.text

    def test_collapsed_answers_still_parsed(self) -> None:
        result = parse_quora_question(_COLLAPSED_HTML, _COLLAPSED_URL)
        assert len(result.answers) == 2

    def test_collapsed_answer_has_truncated_flag(self) -> None:
        result = parse_quora_question(_COLLAPSED_HTML, _COLLAPSED_URL)
        truncated = [a for a in result.answers if a.truncated]
        assert len(truncated) >= 1

    def test_extracts_question_title_with_collapsed(self) -> None:
        result = parse_quora_question(_COLLAPSED_HTML, _COLLAPSED_URL)
        assert "productive" in result.title


class TestToExtractedContent:
    """QuoraQuestion converts to ExtractedContent contract."""

    def test_converts_to_extracted_content(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        content = result.to_extracted_content()

        assert isinstance(content, ExtractedContent)
        assert content.url == _QUESTION_URL
        assert "best programming language" in content.title
        assert len(content.comments) >= 1

    def test_body_contains_top_answer(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        content = result.to_extracted_content()
        assert "Python" in content.body

    def test_comments_include_author_and_upvotes(self) -> None:
        result = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        content = result.to_extracted_content()
        first_comment = content.comments[0]
        assert "Sarah Tech" in first_comment
        assert "987" in first_comment


class TestFallbackBehavior:
    """Falls back gracefully on non-Quora or broken HTML."""

    def test_fallback_on_non_quora_html(self) -> None:
        html = "<html><body><p>Just a normal page</p></body></html>"
        result = parse_quora_question(html, _QUESTION_URL)
        assert result.title == ""
        assert result.followers_count == 0
        assert result.answers == ()

    def test_fallback_on_empty_html(self) -> None:
        result = parse_quora_question("", _QUESTION_URL)
        assert result.title == ""
        assert result.answers == ()


class TestCaching:
    """Same URL + HTML returns cached result."""

    def test_same_input_returns_cached_result(self) -> None:
        result1 = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        result2 = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        assert result1 == result2

    def test_different_url_returns_different_result(self) -> None:
        result1 = parse_quora_question(_QUESTION_HTML, _QUESTION_URL)
        result2 = parse_quora_question(_COLLAPSED_HTML, _COLLAPSED_URL)
        assert result1 != result2
