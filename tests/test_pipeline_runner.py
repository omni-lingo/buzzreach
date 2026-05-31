"""Tests for PIPE-001: Tiered pipeline orchestrator.

Covers: full pipeline happy path, already-seen skip, scoring gate,
stage order (AD-6), metrics recording, multiple candidates.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from contracts.config.product_config import ProductConfig
from contracts.discovery.candidate import Candidate
from contracts.extraction.extracted_content import ExtractedContent
from contracts.opportunity.opportunity import OpportunityData
from contracts.scoring.relevance import RelevanceResult
from src.backend.db.base import Base
from src.backend.models.opportunity import Opportunity
from src.backend.services.pipeline.runner import PipelineDeps, run_pipeline


@pytest.fixture()
def db_session() -> Session:
    """In-memory SQLite session with the buzzreach schema attached."""
    engine = create_engine(
        "sqlite:///:memory:",
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


def _cfg() -> ProductConfig:
    return ProductConfig(
        slug="irs-calculator",
        product_url="https://irscalculator.example.com",
        pitch="Calculate your IRS penalty reduction in 60 seconds",
        niche="tax",
        keywords=["IRS penalty", "CP14", "tax help"],
        tone="helpful and empathetic",
        mention="IRS Penalty Calculator",
    )


def _cand(url: str = "https://reddit.com/r/tax/abc") -> Candidate:
    return Candidate(
        url=url, title="Help with IRS CP14 notice",
        snippet="Need help with tax penalty CP14",
        source="reddit.com", found_at=datetime(2026, 1, 15, 12, 0, 0),
    )


def _extracted() -> ExtractedContent:
    return ExtractedContent(
        url="https://reddit.com/r/tax/abc",
        title="Help with IRS CP14 notice",
        body="I received a CP14 notice for $500.",
        comments=["Try calling the IRS"],
    )


def _pass_score() -> RelevanceResult:
    return RelevanceResult(
        score=0.85, is_seeking_help=True,
        angle_already_covered=False,
        reason="User needs penalty help, no calculator mentioned.",
    )


def _score(
    val: float = 0.85,
    seeking: bool = True,
    covered: bool = False,
    reason: str = "test",
) -> RelevanceResult:
    return RelevanceResult(
        score=val, is_seeking_help=seeking,
        angle_already_covered=covered, reason=reason,
    )


def _deps(
    candidates: list[Candidate] | None = None,
    score_result: RelevanceResult | None = None,
    draft_text: str = "Here is a helpful reply.",
) -> PipelineDeps:
    """Build PipelineDeps with all mocked callables."""
    return PipelineDeps(
        discover_fn=MagicMock(
            return_value=(
                candidates if candidates is not None
                else [_cand()]
            ),
        ),
        filter_unseen_fn=MagicMock(
            side_effect=lambda cands, niche, session: cands,
        ),
        keyword_match_fn=MagicMock(
            side_effect=lambda cands, config: cands,
        ),
        extract_fn=MagicMock(return_value=_extracted()),
        score_fn=MagicMock(
            return_value=score_result or _pass_score(),
        ),
        draft_fn=MagicMock(return_value=draft_text),
        mark_seen_fn=MagicMock(),
        audit_service=MagicMock(),
        metrics_recorder=MagicMock(),
    )


class TestFullPipelineHappyPath:
    """Seeking-help candidate -> Opportunity + audit + seen_urls."""

    def test_produces_opportunity(self, db_session: Session) -> None:
        results = run_pipeline(_cfg(), _deps(), db_session)
        assert len(results) == 1
        assert isinstance(results[0], OpportunityData)
        assert results[0].niche == "tax"
        assert results[0].draft_reply == "Here is a helpful reply."

    def test_persists_opportunity_row(self, db_session: Session) -> None:
        run_pipeline(_cfg(), _deps(), db_session)
        rows = db_session.execute(select(Opportunity)).scalars().all()
        assert len(rows) == 1
        assert rows[0].niche == "tax"
        assert rows[0].relevance_score == 0.85

    def test_calls_mark_seen(self, db_session: Session) -> None:
        deps = _deps()
        run_pipeline(_cfg(), deps, db_session)
        deps.mark_seen_fn.assert_called_once()
        kw = deps.mark_seen_fn.call_args.kwargs
        assert kw["url"] == "https://reddit.com/r/tax/abc"
        assert kw["niche"] == "tax"

    def test_logs_audit_event(self, db_session: Session) -> None:
        deps = _deps()
        run_pipeline(_cfg(), deps, db_session)
        deps.audit_service.log.assert_called_once()
        kw = deps.audit_service.log.call_args.kwargs
        assert kw["action"] == "opportunity_generated"

    def test_records_metrics(self, db_session: Session) -> None:
        deps = _deps()
        run_pipeline(_cfg(), deps, db_session)
        names = [c.args[0] for c in deps.metrics_recorder.record.call_args_list]
        assert "candidates_found" in names
        assert "drafts_generated" in names


class TestAlreadySeenSkipsAI:
    """Already-seen candidates never reach AI stages."""

    def test_skips_scoring_and_drafting(self, db_session: Session) -> None:
        deps = _deps()
        deps.filter_unseen_fn = MagicMock(return_value=[])
        run_pipeline(_cfg(), deps, db_session)
        deps.score_fn.assert_not_called()
        deps.draft_fn.assert_not_called()

    def test_skips_extraction(self, db_session: Session) -> None:
        deps = _deps()
        deps.filter_unseen_fn = MagicMock(return_value=[])
        run_pipeline(_cfg(), deps, db_session)
        deps.extract_fn.assert_not_called()

    def test_no_audit_when_all_filtered(self, db_session: Session) -> None:
        deps = _deps()
        deps.filter_unseen_fn = MagicMock(return_value=[])
        run_pipeline(_cfg(), deps, db_session)
        deps.audit_service.log.assert_not_called()


class TestScoringGate:
    """Drafting only runs when score passes the gate."""

    def test_not_seeking_help_skips_draft(self, db_session: Session) -> None:
        deps = _deps(score_result=_score(seeking=False))
        results = run_pipeline(_cfg(), deps, db_session)
        assert len(results) == 0
        deps.draft_fn.assert_not_called()

    def test_angle_covered_skips_draft(self, db_session: Session) -> None:
        deps = _deps(score_result=_score(covered=True))
        results = run_pipeline(_cfg(), deps, db_session)
        assert len(results) == 0
        deps.draft_fn.assert_not_called()

    def test_low_score_skips_draft(self, db_session: Session) -> None:
        deps = _deps(score_result=_score(val=0.3))
        results = run_pipeline(_cfg(), deps, db_session)
        assert len(results) == 0
        deps.draft_fn.assert_not_called()


class TestStageOrder:
    """Stage order matches AD-6: free stages first, expensive last."""

    def test_keyword_filter_before_extract(self, db_session: Session) -> None:
        deps = _deps()
        deps.keyword_match_fn = MagicMock(return_value=[])
        run_pipeline(_cfg(), deps, db_session)
        deps.keyword_match_fn.assert_called_once()
        deps.extract_fn.assert_not_called()
        deps.score_fn.assert_not_called()

    def test_dedup_before_keyword_filter(self, db_session: Session) -> None:
        order: list[str] = []
        deps = _deps()
        deps.filter_unseen_fn = MagicMock(
            side_effect=lambda c, n, s: (order.append("dedup") or c),
        )
        deps.keyword_match_fn = MagicMock(
            side_effect=lambda c, cfg: (order.append("keyword") or c),
        )
        run_pipeline(_cfg(), deps, db_session)
        assert order.index("dedup") < order.index("keyword")


class TestMultipleCandidates:
    """Pipeline handles multiple candidates correctly."""

    def test_mixed_pass_and_fail(self, db_session: Session) -> None:
        deps = _deps(candidates=[_cand("https://r.com/1"), _cand("https://r.com/2")])
        deps.extract_fn = MagicMock(return_value=_extracted())
        deps.score_fn = MagicMock(side_effect=[_pass_score(), _score(val=0.2, seeking=False)])
        results = run_pipeline(_cfg(), deps, db_session)
        assert len(results) == 1
        assert deps.draft_fn.call_count == 1

    def test_empty_discovery(self, db_session: Session) -> None:
        deps = _deps(candidates=[])
        results = run_pipeline(_cfg(), deps, db_session)
        assert results == []
        deps.extract_fn.assert_not_called()
