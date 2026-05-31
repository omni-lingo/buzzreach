"""Niche bundle service for listing and applying bundles (QUALITY-004).

Pure business logic with no HTTP dependencies. Database access via
injected Session. Raises AppError for recoverable failures.

Cross-module contracts:
- Creates SearchProfile (FEAT-004) when a bundle is applied
- References template format (QUALITY-003)
- Helps onboarding flow (ONBOARD-003)
"""

import logging
import uuid as _uuid

from sqlalchemy.orm import Session

from contracts.quality.niche_bundle import (
    ApplyBundleRequest,
    ApplyBundleResponse,
)
from src.backend.errors import AppError
from src.backend.models.niche_bundle import NicheBundle
from src.backend.models.search_profile import SearchProfile
from src.backend.services.quality.seed_bundles_extra import LIFESTYLE_BUNDLES
from src.backend.services.quality.seed_bundles_professional import (
    PROFESSIONAL_BUNDLES,
)
from src.backend.services.quality.seed_bundles_tech import TECH_BUNDLES

log = logging.getLogger("buzzreach.quality.niche_bundles")

ALL_SEED_BUNDLES = PROFESSIONAL_BUNDLES + TECH_BUNDLES + LIFESTYLE_BUNDLES


class NicheBundleService:
    """Manages niche bundle listing, retrieval, and application."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_bundles(self) -> list[NicheBundle]:
        """List all available niche bundles ordered by name."""
        return list(
            self._session.query(NicheBundle)
            .order_by(NicheBundle.name)
            .all()
        )

    def get_bundle(self, bundle_id: _uuid.UUID) -> NicheBundle:
        """Fetch a single bundle by ID or raise BUNDLE_NOT_FOUND."""
        bundle = self._session.get(NicheBundle, bundle_id)
        if bundle is None:
            raise AppError(
                code="BUNDLE_NOT_FOUND",
                message="Bundle not found",
            )
        return bundle

    def apply_bundle(
        self,
        req: ApplyBundleRequest,
        user_id: _uuid.UUID,
    ) -> ApplyBundleResponse:
        """Apply a bundle to create a new search profile.

        Uses bundle defaults for keywords/platforms unless overridden
        in the request.
        """
        bundle = self.get_bundle(req.bundle_id)

        keywords = req.keywords if req.keywords is not None else bundle.keywords
        platforms = (
            req.platforms if req.platforms is not None else bundle.platforms
        )

        profile = SearchProfile(
            user_id=user_id,
            name=req.profile_name,
            keywords=keywords,
            platforms=platforms,
            languages=["en"],
            enabled=True,
        )
        self._session.add(profile)
        self._session.commit()

        log.info(
            "Bundle applied",
            extra={
                "bundle_id": str(bundle.id),
                "profile_id": str(profile.id),
                "user_id": str(user_id),
            },
        )

        return ApplyBundleResponse(
            profile_id=profile.id,
            profile_name=profile.name,
            bundle_name=bundle.name,
            keywords=keywords,
            platforms=platforms,
            message=f"Profile created from '{bundle.name}' bundle",
        )

    def seed_bundles(self) -> None:
        """Insert seed bundles if they don't already exist.

        Idempotent: skips bundles whose slug already exists.
        """
        existing_slugs = {
            b.slug
            for b in self._session.query(NicheBundle).all()
        }

        for seed in ALL_SEED_BUNDLES:
            if seed.slug in existing_slugs:
                continue
            bundle = NicheBundle(
                name=seed.name,
                slug=seed.slug,
                description=seed.description,
                keywords=seed.keywords,
                platforms=seed.platforms,
                tone=seed.tone,
                tone_description=seed.tone_description,
                templates=[
                    {
                        "name": t.name,
                        "category": t.category,
                        "description": t.description,
                        "text": t.text,
                    }
                    for t in seed.templates
                ],
                icon=seed.icon,
            )
            self._session.add(bundle)

        self._session.commit()
        log.info("Niche bundles seeded")
