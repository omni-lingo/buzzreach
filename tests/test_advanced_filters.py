"""Tests for the advanced filter service (FEAT-002).

Covers: regex_filter, not_filter, field_filter, composite_filter,
plan limit enforcement, invalid regex rejection, and FilterRule model.
"""

import uuid
from datetime import UTC, datetime

from contracts.features.filter_rule import FILTER_RULE_LIMITS, RuleType
from src.backend.models.filter_rule import FilterRule
from src.backend.models.opportunity import Opportunity
from src.backend.services.advanced_filter_service import (
    composite_filter,
    field_filter,
    not_filter,
    regex_filter,
    validate_regex_patterns,
)


def _make_opp(**overrides: object) -> Opportunity:
    """Build an Opportunity with sensible defaults for filter tests."""
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "niche": "saas",
        "url": "https://reddit.com/r/saas/post1",
        "title": "Looking for a project management tool",
        "source": "reddit",
        "why_matched": "mentions project management",
        "relevance_score": 0.8,
        "draft_reply": "Check out our tool...",
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return Opportunity(**defaults)


def _sample_opportunities() -> list[Opportunity]:
    """Build a list of varied opportunities for filter tests."""
    return [
        _make_opp(
            url="https://reddit.com/r/saas/abc",
            title="Best CRM for startups",
            source="reddit",
            relevance_score=0.9,
        ),
        _make_opp(
            url="https://quora.com/what-is-best-crm",
            title="What is the best CRM?",
            source="quora",
            relevance_score=0.7,
        ),
        _make_opp(
            url="https://reddit.com/r/spam/xyz",
            title="FREE MONEY CLICK HERE",
            source="reddit",
            relevance_score=0.3,
        ),
        _make_opp(
            url="https://hn.com/item?id=123",
            title="Show HN: New dev tool for teams",
            source="hackernews",
            relevance_score=0.85,
        ),
        _make_opp(
            url="https://reddit.com/r/marketing/post5",
            title="Hiring a marketing consultant",
            source="reddit",
            relevance_score=0.6,
        ),
    ]


class TestRegexFilter:
    """Tests for regex_filter — reject if URL/title/content matches."""

    def test_rejects_matching_urls(self) -> None:
        opps = _sample_opportunities()
        patterns = [r"reddit\.com/r/spam"]
        result = regex_filter(opps, patterns)
        assert len(result) == 4
        urls = [o.url for o in result]
        assert all("r/spam" not in u for u in urls)

    def test_rejects_matching_titles(self) -> None:
        opps = _sample_opportunities()
        patterns = [r"FREE\s+MONEY"]
        result = regex_filter(opps, patterns)
        assert len(result) == 4

    def test_no_match_returns_all(self) -> None:
        opps = _sample_opportunities()
        patterns = [r"nonexistent_pattern_xyz"]
        result = regex_filter(opps, patterns)
        assert len(result) == 5

    def test_empty_patterns_returns_all(self) -> None:
        opps = _sample_opportunities()
        result = regex_filter(opps, [])
        assert len(result) == 5

    def test_multiple_patterns_union(self) -> None:
        opps = _sample_opportunities()
        patterns = [r"reddit\.com/r/spam", r"quora\.com"]
        result = regex_filter(opps, patterns)
        assert len(result) == 3


class TestNotFilter:
    """Tests for not_filter — case-insensitive keyword exclusion."""

    def test_excludes_keyword(self) -> None:
        opps = _sample_opportunities()
        result = not_filter(opps, ["hiring"])
        assert len(result) == 4

    def test_case_insensitive(self) -> None:
        opps = _sample_opportunities()
        result = not_filter(opps, ["HIRING"])
        assert len(result) == 4

    def test_no_keywords_returns_all(self) -> None:
        opps = _sample_opportunities()
        result = not_filter(opps, [])
        assert len(result) == 5

    def test_multiple_keywords(self) -> None:
        opps = _sample_opportunities()
        result = not_filter(opps, ["hiring", "free money"])
        assert len(result) == 3


class TestFieldFilter:
    """Tests for field_filter — filter by score, platform, age, domain."""

    def test_filter_by_min_score(self) -> None:
        opps = _sample_opportunities()
        filters = {"min_score": 0.8}
        result = field_filter(opps, filters)
        assert len(result) == 2
        assert all(o.relevance_score >= 0.8 for o in result)

    def test_filter_by_max_score(self) -> None:
        opps = _sample_opportunities()
        filters = {"max_score": 0.5}
        result = field_filter(opps, filters)
        assert len(result) == 1
        assert result[0].relevance_score == 0.3

    def test_filter_by_platform(self) -> None:
        opps = _sample_opportunities()
        filters = {"platforms": ["reddit"]}
        result = field_filter(opps, filters)
        assert len(result) == 3
        assert all(o.source == "reddit" for o in result)

    def test_filter_by_multiple_platforms(self) -> None:
        opps = _sample_opportunities()
        filters = {"platforms": ["reddit", "quora"]}
        result = field_filter(opps, filters)
        assert len(result) == 4

    def test_filter_by_domain(self) -> None:
        opps = _sample_opportunities()
        filters = {"exclude_domains": ["quora.com"]}
        result = field_filter(opps, filters)
        assert len(result) == 4

    def test_combined_field_filters(self) -> None:
        opps = _sample_opportunities()
        filters = {"min_score": 0.5, "platforms": ["reddit"]}
        result = field_filter(opps, filters)
        assert len(result) == 2


class TestCompositeFilter:
    """Tests for composite_filter — AND/OR/NOT logic."""

    def test_and_logic(self) -> None:
        opps = _sample_opportunities()
        rules: list[dict[str, object]] = [
            {"type": "field", "config": {"min_score": 0.5}},
            {"type": "field", "config": {"platforms": ["reddit"]}},
        ]
        result = composite_filter(opps, rules, logic="AND")
        assert len(result) == 2

    def test_or_logic(self) -> None:
        opps = _sample_opportunities()
        rules: list[dict[str, object]] = [
            {"type": "field", "config": {"platforms": ["hackernews"]}},
            {"type": "field", "config": {"platforms": ["quora"]}},
        ]
        result = composite_filter(opps, rules, logic="OR")
        assert len(result) == 2

    def test_not_logic(self) -> None:
        opps = _sample_opportunities()
        rules: list[dict[str, object]] = [
            {"type": "not", "config": {"keywords": ["hiring"]}},
        ]
        result = composite_filter(opps, rules, logic="AND")
        assert len(result) == 4


class TestValidateRegex:
    """Tests for regex validation — invalid regex rejected with error."""

    def test_valid_patterns(self) -> None:
        errors = validate_regex_patterns([r"reddit\.com", r"\bfoo\b"])
        assert errors == []

    def test_invalid_pattern(self) -> None:
        errors = validate_regex_patterns([r"[invalid"])
        assert len(errors) == 1
        assert "invalid" in errors[0].lower() or "[" in errors[0]

    def test_mixed_valid_invalid(self) -> None:
        errors = validate_regex_patterns([r"valid", r"(unclosed"])
        assert len(errors) == 1


class TestFilterRuleModel:
    """Tests for the FilterRule ORM model persistence."""

    def test_create_filter_rule(self, db_session) -> None:  # type: ignore[no-untyped-def]
        from tests.conftest import make_user

        user = make_user()
        db_session.add(user)
        db_session.commit()

        rule = FilterRule(
            user_id=user.id,
            name="Block spam subreddits",
            rule_type=RuleType.REGEX,
            patterns={"regex": [r"reddit\.com/r/spam"]},
            description="Rejects posts from spam subreddit",
        )
        db_session.add(rule)
        db_session.commit()

        loaded = db_session.query(FilterRule).filter_by(id=rule.id).one()
        assert loaded.name == "Block spam subreddits"
        assert loaded.rule_type == "regex"
        assert loaded.enabled is True

    def test_rule_type_values(self) -> None:
        assert RuleType.REGEX == "regex"
        assert RuleType.NOT == "not"
        assert RuleType.FIELD == "field"
        assert RuleType.COMPOSITE == "composite"

    def test_plan_limits_defined(self) -> None:
        assert FILTER_RULE_LIMITS["free"] == 3
        assert FILTER_RULE_LIMITS["pro"] == 20
        assert FILTER_RULE_LIMITS["premium"] == 100
