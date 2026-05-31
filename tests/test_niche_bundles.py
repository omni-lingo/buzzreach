"""Tests for niche bundle model, service, and apply flow (QUALITY-004).

Covers:
- NicheBundle model CRUD
- NicheBundleService list/get/apply logic
- Seed bundles loading (10+ niches)
- Apply bundle creates a SearchProfile with correct data
- Bundle customization on apply (override keywords/platforms)
- Contract type validation
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from contracts.quality.niche_bundle import (
    ApplyBundleRequest,
    BundleTemplate,
    NicheBundleData,
)
from src.backend.errors import AppError
from src.backend.models.niche_bundle import NicheBundle
from src.backend.models.search_profile import SearchProfile
from src.backend.services.quality.niche_bundle_service import (
    NicheBundleService,
)
from tests.conftest import make_user


class TestNicheBundleModel:
    """Unit tests for NicheBundle ORM model."""

    def test_create_bundle(self, db_session: Session) -> None:
        bundle = NicheBundle(
            name="Legal Services",
            slug="legal-services",
            description="For legal advice threads",
            keywords=["lawsuit advice", "legal help"],
            platforms=["Reddit r/legaladvice", "Avvo"],
            tone="professional",
            tone_description="Careful, authoritative tone",
            templates=[
                {
                    "name": "Legal Reply",
                    "category": "professional",
                    "description": "For legal threads",
                    "text": "I can share perspective on {product_name}.",
                }
            ],
            icon="scale",
        )
        db_session.add(bundle)
        db_session.commit()

        row = db_session.get(NicheBundle, bundle.id)
        assert row is not None
        assert row.name == "Legal Services"
        assert row.slug == "legal-services"
        assert len(row.keywords) == 2
        assert len(row.platforms) == 2

    def test_bundle_has_timestamps(self, db_session: Session) -> None:
        bundle = NicheBundle(
            name="SaaS",
            slug="saas",
            description="SaaS niche",
            keywords=["alternative to"],
            platforms=["Reddit r/SaaS"],
            tone="friendly",
            tone_description="Conversational and helpful",
            templates=[],
            icon="cloud",
        )
        db_session.add(bundle)
        db_session.commit()

        assert bundle.created_at is not None
        assert bundle.updated_at is not None

    def test_bundle_contract_validation(
        self, db_session: Session
    ) -> None:
        bundle = NicheBundle(
            name="E-commerce",
            slug="ecommerce",
            description="E-commerce niche",
            keywords=["where to buy"],
            platforms=["Reddit r/ecommerce"],
            tone="friendly",
            tone_description="Warm and approachable",
            templates=[
                {
                    "name": "Shop Reply",
                    "category": "casual",
                    "description": "Shopping reply",
                    "text": "Check out {product_name}!",
                }
            ],
            icon="cart",
        )
        db_session.add(bundle)
        db_session.commit()

        data = NicheBundleData.model_validate(bundle)
        assert data.name == "E-commerce"
        assert len(data.templates) == 1
        assert isinstance(data.templates[0], BundleTemplate)


class TestNicheBundleService:
    """Unit tests for NicheBundleService business logic."""

    def test_seed_bundles(self, db_session: Session) -> None:
        svc = NicheBundleService(db_session)
        svc.seed_bundles()

        bundles = svc.list_bundles()
        assert len(bundles) >= 10

    def test_seed_bundles_idempotent(
        self, db_session: Session
    ) -> None:
        svc = NicheBundleService(db_session)
        svc.seed_bundles()
        count_1 = len(svc.list_bundles())

        svc.seed_bundles()
        count_2 = len(svc.list_bundles())

        assert count_1 == count_2

    def test_list_bundles(self, db_session: Session) -> None:
        svc = NicheBundleService(db_session)
        svc.seed_bundles()

        bundles = svc.list_bundles()
        assert len(bundles) >= 10
        for b in bundles:
            assert b.name
            assert len(b.keywords) >= 1
            assert len(b.platforms) >= 1
            assert b.tone

    def test_get_bundle_by_id(self, db_session: Session) -> None:
        svc = NicheBundleService(db_session)
        svc.seed_bundles()

        bundles = svc.list_bundles()
        bundle = svc.get_bundle(bundles[0].id)
        assert bundle.id == bundles[0].id

    def test_get_bundle_not_found(self, db_session: Session) -> None:
        svc = NicheBundleService(db_session)
        with pytest.raises(AppError, match="Bundle not found"):
            svc.get_bundle(uuid.uuid4())

    def test_each_bundle_has_templates(
        self, db_session: Session
    ) -> None:
        svc = NicheBundleService(db_session)
        svc.seed_bundles()

        for bundle in svc.list_bundles():
            assert len(bundle.templates) >= 2, (
                f"Bundle '{bundle.name}' must have at least 2 templates"
            )

    def test_each_bundle_has_tone_guide(
        self, db_session: Session
    ) -> None:
        svc = NicheBundleService(db_session)
        svc.seed_bundles()

        for bundle in svc.list_bundles():
            assert bundle.tone, f"Bundle '{bundle.name}' missing tone"
            assert bundle.tone_description, (
                f"Bundle '{bundle.name}' missing tone_description"
            )

    def test_apply_bundle_creates_profile(
        self, db_session: Session
    ) -> None:
        user = make_user()
        db_session.add(user)
        db_session.commit()

        svc = NicheBundleService(db_session)
        svc.seed_bundles()

        bundles = svc.list_bundles()
        req = ApplyBundleRequest(
            bundle_id=bundles[0].id,
            profile_name="My Legal Profile",
        )
        result = svc.apply_bundle(req, user_id=user.id)

        assert result.profile_name == "My Legal Profile"
        assert result.bundle_name == bundles[0].name
        assert len(result.keywords) >= 1
        assert len(result.platforms) >= 1

        profile = (
            db_session.query(SearchProfile)
            .filter_by(id=result.profile_id)
            .one()
        )
        assert profile.user_id == user.id
        assert profile.keywords == result.keywords

    def test_apply_bundle_with_custom_keywords(
        self, db_session: Session
    ) -> None:
        user = make_user()
        db_session.add(user)
        db_session.commit()

        svc = NicheBundleService(db_session)
        svc.seed_bundles()

        bundles = svc.list_bundles()
        custom_kw = ["my custom keyword", "another keyword"]
        req = ApplyBundleRequest(
            bundle_id=bundles[0].id,
            profile_name="Custom Profile",
            keywords=custom_kw,
        )
        result = svc.apply_bundle(req, user_id=user.id)
        assert result.keywords == custom_kw

    def test_apply_bundle_with_custom_platforms(
        self, db_session: Session
    ) -> None:
        user = make_user()
        db_session.add(user)
        db_session.commit()

        svc = NicheBundleService(db_session)
        svc.seed_bundles()

        bundles = svc.list_bundles()
        custom_platforms = ["Reddit r/custom"]
        req = ApplyBundleRequest(
            bundle_id=bundles[0].id,
            profile_name="Custom Platforms",
            platforms=custom_platforms,
        )
        result = svc.apply_bundle(req, user_id=user.id)
        assert result.platforms == custom_platforms

    def test_apply_bundle_not_found(
        self, db_session: Session
    ) -> None:
        user = make_user()
        db_session.add(user)
        db_session.commit()

        svc = NicheBundleService(db_session)
        req = ApplyBundleRequest(
            bundle_id=uuid.uuid4(),
            profile_name="Ghost",
        )
        with pytest.raises(AppError, match="Bundle not found"):
            svc.apply_bundle(req, user_id=user.id)
