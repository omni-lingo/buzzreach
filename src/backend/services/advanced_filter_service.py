"""Advanced filter service for opportunity filtering (FEAT-002).

Pure business logic — no HTTP concerns. Provides regex, NOT, field, and
composite filter functions that operate on lists of Opportunity objects.

Cross-module contracts:
- Reads Opportunity model from CORE-003
- Produces FilterRuleData consumed by PIPE-001
- Respects plan limits from contracts/features/filter_rule.py
"""

import logging
import re
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.orm import Session

from contracts.features.filter_rule import FILTER_RULE_LIMITS, FilterTestResult
from src.backend.errors import AppError
from src.backend.models.filter_rule import FilterRule
from src.backend.models.opportunity import Opportunity

log = logging.getLogger("buzzreach.filters")


def regex_filter(
    opportunities: list[Opportunity],
    patterns: list[str],
) -> list[Opportunity]:
    """Reject opportunities whose URL or title matches any regex pattern."""
    if not patterns:
        return list(opportunities)

    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]

    def _matches(opp: Opportunity) -> bool:
        return any(
            regex.search(opp.url) or regex.search(opp.title)
            for regex in compiled
        )

    return [o for o in opportunities if not _matches(o)]


def not_filter(
    opportunities: list[Opportunity],
    keywords: list[str],
) -> list[Opportunity]:
    """Exclude opportunities containing any of the keywords (case-insensitive)."""
    if not keywords:
        return list(opportunities)

    lower_keywords = [k.lower() for k in keywords]

    def _contains_keyword(opp: Opportunity) -> bool:
        text = f"{opp.title} {opp.why_matched}".lower()
        return any(kw in text for kw in lower_keywords)

    return [o for o in opportunities if not _contains_keyword(o)]


def field_filter(
    opportunities: list[Opportunity],
    filters: dict[str, Any],
) -> list[Opportunity]:
    """Filter opportunities by score range, platform, and domain."""
    result = list(opportunities)
    result = _apply_score_filters(result, filters)
    result = _apply_platform_filter(result, filters)
    result = _apply_domain_filter(result, filters)
    return result


def _apply_score_filters(
    opps: list[Opportunity],
    filters: dict[str, Any],
) -> list[Opportunity]:
    """Apply min_score and max_score filters."""
    min_score = filters.get("min_score")
    max_score = filters.get("max_score")
    result = opps
    if min_score is not None:
        result = [o for o in result if o.relevance_score >= min_score]
    if max_score is not None:
        result = [o for o in result if o.relevance_score <= max_score]
    return result


def _apply_platform_filter(
    opps: list[Opportunity],
    filters: dict[str, Any],
) -> list[Opportunity]:
    """Filter by allowed platform sources."""
    platforms = filters.get("platforms")
    if not platforms:
        return opps
    platform_set = set(platforms)
    return [o for o in opps if o.source in platform_set]


def _apply_domain_filter(
    opps: list[Opportunity],
    filters: dict[str, Any],
) -> list[Opportunity]:
    """Exclude opportunities from specified domains."""
    exclude_domains = filters.get("exclude_domains")
    if not exclude_domains:
        return opps
    domain_set = {d.lower() for d in exclude_domains}

    def _domain_blocked(opp: Opportunity) -> bool:
        host = urlparse(opp.url).hostname or ""
        return any(d in host for d in domain_set)

    return [o for o in opps if not _domain_blocked(o)]


def composite_filter(
    opportunities: list[Opportunity],
    rules: list[dict[str, object]],
    logic: str = "AND",
) -> list[Opportunity]:
    """Combine multiple filter rules with AND/OR logic."""
    if not rules:
        return list(opportunities)

    if logic == "AND":
        return _composite_and(opportunities, rules)
    return _composite_or(opportunities, rules)


def _composite_and(
    opps: list[Opportunity],
    rules: list[dict[str, object]],
) -> list[Opportunity]:
    """Apply all rules sequentially (AND logic)."""
    result = list(opps)
    for rule in rules:
        result = _apply_single_rule(result, rule)
    return result


def _composite_or(
    opps: list[Opportunity],
    rules: list[dict[str, object]],
) -> list[Opportunity]:
    """Keep opportunities that pass ANY rule (OR logic)."""
    passing_ids: set[Any] = set()
    for rule in rules:
        passed = _apply_single_rule(list(opps), rule)
        passing_ids.update(o.id for o in passed)
    return [o for o in opps if o.id in passing_ids]


def _apply_single_rule(
    opps: list[Opportunity],
    rule: dict[str, object],
) -> list[Opportunity]:
    """Dispatch a single rule by type."""
    rule_type = str(rule.get("type", ""))
    config = rule.get("config", {})
    if not isinstance(config, dict):
        return opps

    if rule_type == "regex":
        return regex_filter(opps, config.get("regex", []))
    if rule_type == "not":
        return not_filter(opps, config.get("keywords", []))
    if rule_type == "field":
        return field_filter(opps, config)
    return opps


def validate_regex_patterns(patterns: list[str]) -> list[str]:
    """Validate regex patterns and return list of error messages."""
    errors: list[str] = []
    for pattern in patterns:
        try:
            re.compile(pattern)
        except re.error as exc:
            errors.append(f"Invalid regex '{pattern}': {exc}")
    return errors


def apply_user_rules(
    session: Session,
    user_id: UUID,
    opportunities: list[Opportunity],
) -> list[Opportunity]:
    """Apply all enabled filter rules for a user to a list of opportunities."""
    rules = (
        session.query(FilterRule)
        .filter_by(user_id=user_id, enabled=True)
        .order_by(FilterRule.created_at)
        .all()
    )

    result = list(opportunities)
    for rule in rules:
        result = _apply_stored_rule(result, rule)
        log.info(
            "Filter rule applied",
            extra={
                "rule_id": str(rule.id),
                "rule_name": rule.name,
                "remaining": len(result),
            },
        )
    return result


def _apply_stored_rule(
    opps: list[Opportunity],
    rule: FilterRule,
) -> list[Opportunity]:
    """Apply a persisted FilterRule to opportunities."""
    patterns = rule.patterns or {}
    rule_dict: dict[str, object] = {
        "type": rule.rule_type,
        "config": patterns,
    }
    return _apply_single_rule(opps, rule_dict)


def test_rule_against_opportunities(
    opportunities: list[Opportunity],
    rule_type: str,
    patterns: dict[str, Any],
) -> FilterTestResult:
    """Test a rule config against opportunities, returning match stats."""
    rule_dict: dict[str, object] = {"type": rule_type, "config": patterns}
    passed = _apply_single_rule(list(opportunities), rule_dict)
    passed_ids = {o.id for o in passed}
    rejected = [o for o in opportunities if o.id not in passed_ids]

    sample = [
        {"url": o.url, "title": o.title}
        for o in rejected[:5]
    ]

    return FilterTestResult(
        total=len(opportunities),
        matched=len(passed),
        rejected=len(rejected),
        sample_rejected=sample,
    )


def check_rule_limit(
    session: Session,
    user_id: UUID,
    plan_id: str,
) -> None:
    """Raise AppError if the user has reached their plan's rule limit."""
    limit = FILTER_RULE_LIMITS.get(plan_id, 3)
    count = session.query(FilterRule).filter_by(user_id=user_id).count()
    if count >= limit:
        raise AppError(
            code="RULE_LIMIT_REACHED",
            message=f"Plan '{plan_id}' allows max {limit} filter rules",
        )
