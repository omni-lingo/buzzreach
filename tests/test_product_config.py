"""Tests for ProductConfig contract (CFG-001).

Validates that ProductConfig enforces strict typing: valid configs parse,
missing keywords / bad URLs / empty slugs / invalid freshness are rejected.
"""

import pytest
from pydantic import ValidationError

from contracts.config.product_config import ProductConfig


def _valid_data() -> dict:
    """Return a minimal valid ProductConfig dict."""
    return {
        "slug": "irs-calculator",
        "product_url": "https://example.com/product",
        "pitch": "Calculate IRS penalties instantly",
        "niche": "tax",
        "keywords": ["irs penalty", "cp14 notice"],
        "tone": "helpful and empathetic",
        "mention": "IRS Penalty Calculator at example.com",
    }


class TestProductConfigValid:
    """Valid configurations parse without error."""

    def test_minimal_valid_config(self) -> None:
        cfg = ProductConfig(**_valid_data())
        assert cfg.slug == "irs-calculator"
        assert str(cfg.product_url) == "https://example.com/product"
        assert cfg.keywords == ["irs penalty", "cp14 notice"]

    def test_defaults_applied(self) -> None:
        cfg = ProductConfig(**_valid_data())
        assert cfg.freshness == "d"
        assert cfg.max_queries == 5

    def test_freshness_hour(self) -> None:
        data = _valid_data()
        data["freshness"] = "h"
        cfg = ProductConfig(**data)
        assert cfg.freshness == "h"

    def test_freshness_week(self) -> None:
        data = _valid_data()
        data["freshness"] = "w"
        cfg = ProductConfig(**data)
        assert cfg.freshness == "w"

    def test_max_queries_override(self) -> None:
        data = _valid_data()
        data["max_queries"] = 10
        cfg = ProductConfig(**data)
        assert cfg.max_queries == 10

    def test_single_keyword(self) -> None:
        data = _valid_data()
        data["keywords"] = ["one"]
        cfg = ProductConfig(**data)
        assert cfg.keywords == ["one"]


class TestProductConfigRejectsInvalid:
    """Invalid configurations raise ValidationError with clear messages."""

    def test_empty_keywords_rejected(self) -> None:
        data = _valid_data()
        data["keywords"] = []
        with pytest.raises(ValidationError, match="keywords"):
            ProductConfig(**data)

    def test_missing_keywords_rejected(self) -> None:
        data = _valid_data()
        del data["keywords"]
        with pytest.raises(ValidationError, match="keywords"):
            ProductConfig(**data)

    def test_invalid_url_rejected(self) -> None:
        data = _valid_data()
        data["product_url"] = "not-a-url"
        with pytest.raises(ValidationError, match="product_url"):
            ProductConfig(**data)

    def test_empty_slug_rejected(self) -> None:
        data = _valid_data()
        data["slug"] = ""
        with pytest.raises(ValidationError, match="slug"):
            ProductConfig(**data)

    def test_missing_slug_rejected(self) -> None:
        data = _valid_data()
        del data["slug"]
        with pytest.raises(ValidationError, match="slug"):
            ProductConfig(**data)

    def test_invalid_freshness_rejected(self) -> None:
        data = _valid_data()
        data["freshness"] = "x"
        with pytest.raises(ValidationError, match="freshness"):
            ProductConfig(**data)

    def test_max_queries_zero_rejected(self) -> None:
        data = _valid_data()
        data["max_queries"] = 0
        with pytest.raises(ValidationError, match="max_queries"):
            ProductConfig(**data)

    def test_max_queries_negative_rejected(self) -> None:
        data = _valid_data()
        data["max_queries"] = -1
        with pytest.raises(ValidationError, match="max_queries"):
            ProductConfig(**data)

    def test_extra_fields_rejected(self) -> None:
        data = _valid_data()
        data["unknown_field"] = "should fail"
        with pytest.raises(ValidationError, match="unknown_field"):
            ProductConfig(**data)

    def test_empty_pitch_rejected(self) -> None:
        data = _valid_data()
        data["pitch"] = ""
        with pytest.raises(ValidationError, match="pitch"):
            ProductConfig(**data)

    def test_empty_niche_rejected(self) -> None:
        data = _valid_data()
        data["niche"] = ""
        with pytest.raises(ValidationError, match="niche"):
            ProductConfig(**data)

    def test_empty_tone_rejected(self) -> None:
        data = _valid_data()
        data["tone"] = ""
        with pytest.raises(ValidationError, match="tone"):
            ProductConfig(**data)

    def test_empty_mention_rejected(self) -> None:
        data = _valid_data()
        data["mention"] = ""
        with pytest.raises(ValidationError, match="mention"):
            ProductConfig(**data)
