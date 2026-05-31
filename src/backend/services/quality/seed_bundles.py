"""Niche bundle seed data types and registry (QUALITY-004).

Defines the SeedBundle dataclass and collects all bundles from
domain-specific seed modules.

Cross-module contracts:
- Consumed by NicheBundleService.seed_bundles()
- None — leaf module (seed data only).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SeedBundleTemplate:
    """Template included in a seed bundle."""

    name: str
    category: str
    description: str
    text: str


@dataclass(frozen=True)
class SeedBundle:
    """Definition of a niche bundle to be seeded."""

    name: str
    slug: str
    description: str
    keywords: list[str]
    platforms: list[str]
    tone: str
    tone_description: str
    templates: list[SeedBundleTemplate]
    icon: str = "box"


def _tpl(
    name: str, category: str, desc: str, text: str
) -> SeedBundleTemplate:
    """Shorthand helper to create a SeedBundleTemplate."""
    return SeedBundleTemplate(
        name=name, category=category, description=desc, text=text
    )


NICHE_BUNDLES: list[SeedBundle] = []
