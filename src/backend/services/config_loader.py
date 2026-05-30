"""Config loader service (CFG-002).

Reads per-product JSON config files from a directory, validates each
against the ``ProductConfig`` contract, and returns typed objects.

Consumers: JOB-001 calls ``load_all_configs()`` to drive each scan cycle.
"""

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from contracts.config.product_config import ProductConfig
from src.backend.errors import AppError

log = logging.getLogger("buzzreach.config_loader")


def load_config(slug: str, config_dir: Path) -> ProductConfig:
    """Load and validate a single product config by slug.

    Args:
        slug: File stem (without ``.json``) identifying the config.
        config_dir: Directory containing per-product JSON files.

    Returns:
        A validated ``ProductConfig`` instance.

    Raises:
        AppError: ``CONFIG_NOT_FOUND`` if the file does not exist.
        AppError: ``CONFIG_INVALID`` if JSON parsing or validation fails.
    """
    path = config_dir / f"{slug}.json"
    if not path.is_file():
        raise AppError(
            code="CONFIG_NOT_FOUND",
            message=f"Config file not found: {slug}",
        )
    return _parse_config_file(path)


def load_all_configs(config_dir: Path) -> list[ProductConfig]:
    """Load and validate every ``*.json`` config in the directory.

    Args:
        config_dir: Directory containing per-product JSON files.

    Returns:
        A list of validated ``ProductConfig`` instances.

    Raises:
        AppError: ``CONFIG_INVALID`` if any file fails parsing or validation.
    """
    configs: list[ProductConfig] = []
    for path in sorted(config_dir.glob("*.json")):
        cfg = _parse_config_file(path)
        configs.append(cfg)
        log.info(
            "Loaded product config",
            extra={"slug": cfg.slug, "file": str(path)},
        )
    return configs


def _parse_config_file(path: Path) -> ProductConfig:
    """Read a JSON file and validate it as a ProductConfig.

    Args:
        path: Path to the JSON file.

    Returns:
        A validated ``ProductConfig`` instance.

    Raises:
        AppError: ``CONFIG_INVALID`` on JSON decode or validation error.
    """
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError) as exc:
        raise AppError(
            code="CONFIG_INVALID",
            message=f"Cannot parse config file {path.name}: {exc}",
        ) from exc

    try:
        return ProductConfig(**data)
    except ValidationError as exc:
        raise AppError(
            code="CONFIG_INVALID",
            message=f"Invalid config in {path.name}: {exc}",
        ) from exc
