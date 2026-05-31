"""Tests for keyword_match (FILT-002).

Validates:
- Candidates containing a keyword in title or snippet are kept.
- Unrelated candidates are dropped.
- Matching is case-insensitive.
- Empty inputs are handled correctly.
"""

from datetime import datetime

from contracts.config.product_config import ProductConfig
from contracts.discovery.candidate import Candidate
from src.backend.services.filter.keyword_filter import keyword_match


def _make_candidate(
    title: str = "Generic Title",
    snippet: str = "Generic snippet text",
    url: str = "https://example.com/post",
) -> Candidate:
    return Candidate(
        url=url,
        title=title,
        snippet=snippet,
        source="example.com",
        found_at=datetime(2026, 1, 1),
    )


def _make_config(keywords: list[str]) -> ProductConfig:
    return ProductConfig(
        slug="test-product",
        product_url="https://example.com",
        pitch="A test product",
        niche="testing",
        keywords=keywords,
        tone="helpful",
        mention="TestProduct",
    )


def test_keyword_in_title_kept() -> None:
    candidate = _make_candidate(title="How to deal with IRS penalty")
    config = _make_config(keywords=["IRS penalty"])
    result = keyword_match([candidate], config)
    assert result == [candidate]


def test_keyword_in_snippet_kept() -> None:
    candidate = _make_candidate(snippet="I got a CP14 notice from the IRS")
    config = _make_config(keywords=["CP14 notice"])
    result = keyword_match([candidate], config)
    assert result == [candidate]


def test_unrelated_candidate_dropped() -> None:
    candidate = _make_candidate(
        title="Best recipes for pasta",
        snippet="Try this delicious carbonara recipe",
    )
    config = _make_config(keywords=["IRS penalty", "CP14 notice"])
    result = keyword_match([candidate], config)
    assert result == []


def test_case_insensitive_match() -> None:
    candidate = _make_candidate(title="irs PENALTY help needed")
    config = _make_config(keywords=["IRS Penalty"])
    result = keyword_match([candidate], config)
    assert result == [candidate]


def test_case_insensitive_keyword_in_snippet() -> None:
    candidate = _make_candidate(snippet="Got a cp14 NOTICE yesterday")
    config = _make_config(keywords=["CP14 Notice"])
    result = keyword_match([candidate], config)
    assert result == [candidate]


def test_multiple_candidates_mixed() -> None:
    relevant = _make_candidate(
        title="IRS penalty question",
        url="https://reddit.com/r/tax/1",
    )
    irrelevant = _make_candidate(
        title="Best hiking trails",
        snippet="Beautiful mountain views",
        url="https://reddit.com/r/hiking/2",
    )
    also_relevant = _make_candidate(
        snippet="I received a CP14 notice",
        url="https://reddit.com/r/tax/3",
    )
    config = _make_config(keywords=["IRS penalty", "CP14"])
    result = keyword_match([relevant, irrelevant, also_relevant], config)
    assert result == [relevant, also_relevant]


def test_empty_candidates_returns_empty() -> None:
    config = _make_config(keywords=["IRS penalty"])
    result = keyword_match([], config)
    assert result == []


def test_match_across_title_and_snippet() -> None:
    candidate = _make_candidate(
        title="Need help with taxes",
        snippet="My IRS penalty is huge",
    )
    config = _make_config(keywords=["IRS penalty"])
    result = keyword_match([candidate], config)
    assert result == [candidate]


def test_multiple_keywords_any_matches() -> None:
    candidate = _make_candidate(title="Parking ticket appeal advice")
    config = _make_config(keywords=["IRS penalty", "parking ticket"])
    result = keyword_match([candidate], config)
    assert result == [candidate]


def test_no_duplicate_results_when_both_fields_match() -> None:
    candidate = _make_candidate(
        title="IRS penalty relief",
        snippet="How to reduce IRS penalty",
    )
    config = _make_config(keywords=["IRS penalty"])
    result = keyword_match([candidate], config)
    assert len(result) == 1
    assert result == [candidate]
