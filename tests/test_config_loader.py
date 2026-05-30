"""Tests for config_loader service (CFG-002).

Validates load_config, load_all_configs: valid examples parse,
malformed JSON raises CONFIG_INVALID, missing slug raises CONFIG_NOT_FOUND,
and coded AppError is always used (never bare ValueError).
"""

import json
from pathlib import Path

import pytest

from contracts.config.product_config import ProductConfig
from src.backend.errors import AppError
from src.backend.services.config_loader import load_all_configs, load_config


@pytest.fixture()
def config_dir(tmp_path: Path) -> Path:
    """Return a temporary config directory."""
    return tmp_path


@pytest.fixture()
def _irs_config(config_dir: Path) -> None:
    """Write a valid IRS config file into the temp dir."""
    data = {
        "slug": "irs-penalty-calculator",
        "product_url": "https://irscalculator.example.com",
        "pitch": "Instantly calculate IRS penalties and interest",
        "niche": "tax",
        "keywords": ["irs penalty", "cp14 notice", "tax penalty calculator"],
        "tone": "helpful and empathetic",
        "mention": "IRS Penalty Calculator at irscalculator.example.com",
        "freshness": "d",
        "max_queries": 5,
    }
    (config_dir / "irs_penalty_calculator.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


@pytest.fixture()
def _parking_config(config_dir: Path) -> None:
    """Write a valid ParkingAppealMate config file into the temp dir."""
    data = {
        "slug": "parking-appeal-mate",
        "product_url": "https://parkingappealmate.example.com",
        "pitch": "Fight unfair parking tickets with AI-drafted appeals",
        "niche": "legal-tech",
        "keywords": ["parking ticket appeal", "contest parking fine"],
        "tone": "confident and reassuring",
        "mention": "ParkingAppealMate at parkingappealmate.example.com",
        "freshness": "d",
        "max_queries": 3,
    }
    (config_dir / "parking_appeal_mate.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


class TestLoadConfig:
    """Tests for load_config(slug, config_dir)."""

    @pytest.mark.usefixtures("_irs_config")
    def test_loads_valid_config(self, config_dir: Path) -> None:
        cfg = load_config("irs_penalty_calculator", config_dir)
        assert isinstance(cfg, ProductConfig)
        assert cfg.slug == "irs-penalty-calculator"
        assert cfg.niche == "tax"

    @pytest.mark.usefixtures("_parking_config")
    def test_loads_parking_config(self, config_dir: Path) -> None:
        cfg = load_config("parking_appeal_mate", config_dir)
        assert isinstance(cfg, ProductConfig)
        assert cfg.slug == "parking-appeal-mate"

    def test_missing_slug_raises_config_not_found(
        self, config_dir: Path
    ) -> None:
        with pytest.raises(AppError) as exc_info:
            load_config("nonexistent", config_dir)
        assert exc_info.value.code == "CONFIG_NOT_FOUND"

    def test_malformed_json_raises_config_invalid(
        self, config_dir: Path
    ) -> None:
        (config_dir / "bad.json").write_text("{invalid json", encoding="utf-8")
        with pytest.raises(AppError) as exc_info:
            load_config("bad", config_dir)
        assert exc_info.value.code == "CONFIG_INVALID"

    def test_invalid_schema_raises_config_invalid(
        self, config_dir: Path
    ) -> None:
        data = {"slug": "", "product_url": "not-a-url"}
        (config_dir / "broken.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with pytest.raises(AppError) as exc_info:
            load_config("broken", config_dir)
        assert exc_info.value.code == "CONFIG_INVALID"


class TestLoadAllConfigs:
    """Tests for load_all_configs(config_dir)."""

    @pytest.mark.usefixtures("_irs_config", "_parking_config")
    def test_loads_all_valid_configs(self, config_dir: Path) -> None:
        configs = load_all_configs(config_dir)
        assert len(configs) == 2
        slugs = {c.slug for c in configs}
        assert slugs == {"irs-penalty-calculator", "parking-appeal-mate"}

    def test_empty_dir_returns_empty_list(self, config_dir: Path) -> None:
        configs = load_all_configs(config_dir)
        assert configs == []

    @pytest.mark.usefixtures("_irs_config")
    def test_skips_non_json_files(self, config_dir: Path) -> None:
        (config_dir / "readme.txt").write_text("ignore me", encoding="utf-8")
        configs = load_all_configs(config_dir)
        assert len(configs) == 1

    @pytest.mark.usefixtures("_irs_config")
    def test_raises_on_invalid_file(self, config_dir: Path) -> None:
        (config_dir / "bad.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(AppError) as exc_info:
            load_all_configs(config_dir)
        assert exc_info.value.code == "CONFIG_INVALID"


class TestExampleConfigFiles:
    """Validate the shipped example configs against ProductConfig."""

    @pytest.fixture()
    def examples_dir(self) -> Path:
        return Path("config")

    def test_example_irs_validates(self, examples_dir: Path) -> None:
        path = examples_dir / "example_irs.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        cfg = ProductConfig(**data)
        assert cfg.slug == "irs-penalty-calculator"

    def test_example_parking_validates(self, examples_dir: Path) -> None:
        path = examples_dir / "example_parking.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        cfg = ProductConfig(**data)
        assert cfg.slug == "parking-appeal-mate"
