"""Integration test fixtures (TEST-001).

Provides:
- ``integration_session``: in-memory SQLite with all models migrated.
- ``fake_pipeline_deps``: PipelineDeps with stubbed externals only.
- ``integration_client``: FastAPI TestClient with auth/rate-limit
  overrides wired to the integration session.
- ``fake_settings``: minimal Settings for delivery transports.
"""

import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from contracts.auth.user import UserData
from contracts.config.product_config import ProductConfig
from contracts.discovery.candidate import Candidate
from contracts.extraction.extracted_content import ExtractedContent
from contracts.scoring.relevance import RelevanceResult
from src.backend.api.auth_deps import get_current_user
from src.backend.api.main import create_app
from src.backend.api.rate_limit_middleware import get_rate_limiter
from src.backend.db.base import Base
from src.backend.db.session import get_session
from src.backend.models.user import User
from src.backend.services.auth.audit_service import AuditService
from src.backend.services.auth.rate_limiter import RateLimiter
from src.backend.services.filter.dedup import filter_unseen, mark_seen
from src.backend.services.filter.keyword_filter import keyword_match
from src.backend.services.observability.metrics import MetricsRecorder
from src.backend.services.pipeline.runner import PipelineDeps

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


@pytest.fixture()
def integration_session() -> Generator[Session, None, None]:
    """In-memory SQLite with schema_translate_map for buzzreach."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        execution_options={"schema_translate_map": {"buzzreach": None}},
    )

    @event.listens_for(engine, "connect")
    def _attach(dbapi_conn: object, _rec: object) -> None:
        cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
        cursor.execute("ATTACH DATABASE ':memory:' AS buzzreach")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def test_user(integration_session: Session) -> User:
    """Insert and return an active user for API auth."""
    user = User(
        username="integration_user",
        email="integration@test.com",
        password_hash="hashed_placeholder",
        api_key=f"bz_{uuid.uuid4().hex[:24]}",
    )
    integration_session.add(user)
    integration_session.commit()
    return user


def _make_fake_discover(
    candidates_by_niche: dict[str, list[Candidate]],
) -> Any:
    """Return a discover_fn that yields candidates for the config niche."""
    def discover(config: ProductConfig) -> list[Candidate]:
        return candidates_by_niche.get(config.niche, [])
    return discover


def _make_candidates_for_config(
    config: ProductConfig,
) -> list[Candidate]:
    """Build two fake Candidate objects per config."""
    now = datetime.now(UTC)
    return [
        Candidate(
            url=f"https://reddit.com/r/{config.niche}/post_1",
            title=f"Need help with {config.keywords[0]}",
            snippet=f"Looking for a {config.keywords[0]} solution",
            source="reddit.com",
            found_at=now,
        ),
        Candidate(
            url=f"https://reddit.com/r/{config.niche}/post_2",
            title=f"Best {config.keywords[1]} tools?",
            snippet=f"Any recommendations for {config.keywords[1]}",
            source="reddit.com",
            found_at=now,
        ),
    ]


def _fake_extract(url: str) -> ExtractedContent:
    """Stub extractor: returns synthetic content for any URL."""
    return ExtractedContent(
        url=url,
        title=f"Thread at {url}",
        body="I need help with my problem. Any suggestions?",
        comments=["Try checking the docs", "Same issue here"],
        truncated=False,
    )


def _fake_score(
    content: ExtractedContent,
    config: ProductConfig,
) -> RelevanceResult:
    """Stub scorer: always returns a passing score."""
    return RelevanceResult(
        score=0.85,
        is_seeking_help=True,
        angle_already_covered=False,
        reason=f"User needs help with {config.niche}",
    )


def _fake_draft(
    content: ExtractedContent,
    config: ProductConfig,
) -> str:
    """Stub drafter: returns a deterministic draft reply."""
    return (
        f"Great question! Check out {config.mention} — "
        f"{config.pitch}"
    )


@pytest.fixture()
def fake_pipeline_deps(
    integration_session: Session,
) -> PipelineDeps:
    """PipelineDeps with real dedup/filter but stubbed externals."""
    audit = AuditService(integration_session)
    metrics = MetricsRecorder(integration_session)

    candidates_by_niche: dict[str, list[Candidate]] = {}
    for cfg_path in sorted(CONFIG_DIR.glob("*.json")):
        cfg = ProductConfig.model_validate_json(
            cfg_path.read_text(encoding="utf-8"),
        )
        candidates_by_niche[cfg.niche] = _make_candidates_for_config(cfg)

    return PipelineDeps(
        discover_fn=_make_fake_discover(candidates_by_niche),
        filter_unseen_fn=filter_unseen,
        keyword_match_fn=keyword_match,
        extract_fn=_fake_extract,
        score_fn=_fake_score,
        draft_fn=_fake_draft,
        mark_seen_fn=lambda url, niche, angle_covered=None, **kw: (
            mark_seen(
                url=url,
                niche=niche,
                angle_covered=angle_covered,
                session=integration_session,
            )
        ),
        audit_service=audit,
        metrics_recorder=metrics,
    )


class _FakeSettings:
    """Minimal settings stub with no real SMTP/Slack."""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@test.com"
    slack_webhook_url: str = ""


@pytest.fixture()
def fake_settings() -> _FakeSettings:
    """Settings with delivery transports disabled."""
    return _FakeSettings()


@pytest.fixture()
def integration_client(
    integration_session: Session,
    test_user: User,
) -> TestClient:
    """FastAPI TestClient with auth and rate-limit overrides."""
    app = create_app()

    user_data = UserData(
        id=test_user.id,
        username=test_user.username,
        email=test_user.email,
        is_active=True,
    )

    def _override_session() -> Generator[Session, None, None]:
        yield integration_session

    def _override_user() -> UserData:
        return user_data

    def _override_limiter() -> RateLimiter:
        limiter = MagicMock(spec=RateLimiter)
        limiter.check.return_value = True
        return limiter

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_rate_limiter] = _override_limiter

    return TestClient(app)
