"""Tests for JOB-001: Scheduled scan job.

Covers: run_scan iterates all configs from load_all_configs, calls
run_pipeline per config with injected deps, builds + sends one digest
per scan, audits scan_completed, and returns a ScanReport with correct
counts. Pipeline, sender, audit, and metrics are all mocked.
"""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from contracts.config.product_config import ProductConfig
from contracts.jobs.scan_report import NicheReport, ScanReport
from contracts.opportunity.opportunity import OpportunityData

# -- helpers -----------------------------------------------------------------

_PATCH_BASE = "src.backend.jobs.scan"


def _make_config(**overrides: object) -> ProductConfig:
    """Build a ProductConfig with sensible defaults."""
    defaults: dict[str, object] = {
        "slug": "test-product",
        "product_url": "https://example.com",
        "pitch": "A great product",
        "niche": "tax",
        "keywords": ["irs", "penalty"],
        "tone": "helpful",
        "mention": "Check out ExampleProduct",
    }
    defaults.update(overrides)
    return ProductConfig(**defaults)


def _make_opportunity(niche: str = "tax") -> OpportunityData:
    """Build an OpportunityData DTO with sensible defaults."""
    return OpportunityData(
        id=uuid.uuid4(),
        niche=niche,
        url="https://reddit.com/r/tax/123",
        title="IRS penalty question",
        source="reddit",
        why_matched="Asks about penalty reduction",
        relevance_score=0.9,
        draft_reply="Try first-time abatement.",
        status="new",
        created_at=datetime.now(UTC),
    )


def _run(
    configs: list[ProductConfig],
    pipeline_return: object,
    fetch_return: list[OpportunityData] | None = None,
    audit: MagicMock | None = None,
) -> ScanReport:
    """Patch all externals and run run_scan with given params."""
    from src.backend.jobs.scan import run_scan

    opps = fetch_return if fetch_return is not None else []
    ids = [o.id for o in opps]

    with (
        patch(f"{_PATCH_BASE}.load_all_configs", return_value=configs),
        patch(f"{_PATCH_BASE}.fetch_new_opportunities", return_value=opps),
        patch(f"{_PATCH_BASE}.build_digest") as m_build,
        patch(f"{_PATCH_BASE}.send_digest"),
    ):
        m_build.return_value = MagicMock(opportunity_ids=ids)
        return run_scan(
            config_dir=Path("config"),
            pipeline_fn=pipeline_return,
            session=MagicMock(),
            settings=MagicMock(),
            audit_service=audit or MagicMock(),
            metrics_recorder=MagicMock(),
        )


# -- run_scan: pipeline invocation ------------------------------------------

class TestRunScanProcessesAllConfigs:
    """run_scan calls run_pipeline for every config."""

    def test_processes_two_configs(self) -> None:
        cfg1 = _make_config(slug="prod-a", niche="tax")
        cfg2 = _make_config(slug="prod-b", niche="parking")
        mock_pipeline = MagicMock(return_value=[])

        _run([cfg1, cfg2], mock_pipeline)

        assert mock_pipeline.call_count == 2

    def test_pipeline_receives_config_and_session(self) -> None:
        cfg = _make_config(niche="tax")
        mock_pipeline = MagicMock(return_value=[])

        with (
            patch(f"{_PATCH_BASE}.load_all_configs", return_value=[cfg]),
            patch(f"{_PATCH_BASE}.fetch_new_opportunities", return_value=[]),
            patch(f"{_PATCH_BASE}.build_digest") as m_build,
            patch(f"{_PATCH_BASE}.send_digest"),
        ):
            from src.backend.jobs.scan import run_scan

            m_build.return_value = MagicMock(opportunity_ids=[])
            session = MagicMock()

            run_scan(
                config_dir=Path("config"),
                pipeline_fn=mock_pipeline,
                session=session,
                settings=MagicMock(),
                audit_service=MagicMock(),
                metrics_recorder=MagicMock(),
            )

        call_kw = mock_pipeline.call_args[1]
        assert call_kw["config"] == cfg
        assert call_kw["session"] is session


# -- run_scan: digest delivery -----------------------------------------------

class TestRunScanDigestDelivery:
    """run_scan builds and sends one digest per scan."""

    def test_sends_one_digest(self) -> None:
        cfg = _make_config(niche="tax")
        opp = _make_opportunity()
        mock_pipeline = MagicMock(return_value=[opp])

        with (
            patch(f"{_PATCH_BASE}.load_all_configs", return_value=[cfg]),
            patch(f"{_PATCH_BASE}.fetch_new_opportunities", return_value=[opp]),
            patch(f"{_PATCH_BASE}.build_digest") as m_build,
            patch(f"{_PATCH_BASE}.send_digest") as m_send,
        ):
            from src.backend.jobs.scan import run_scan

            m_build.return_value = MagicMock(opportunity_ids=[opp.id])
            run_scan(
                config_dir=Path("config"),
                pipeline_fn=mock_pipeline,
                session=MagicMock(),
                settings=MagicMock(),
                audit_service=MagicMock(),
                metrics_recorder=MagicMock(),
            )

            m_build.assert_called_once()
            m_send.assert_called_once()


# -- run_scan: audit logging -------------------------------------------------

class TestRunScanAuditLogging:
    """run_scan logs scan_completed to audit after digest send."""

    def test_audits_scan_completed(self) -> None:
        cfg = _make_config(niche="tax")
        opp = _make_opportunity()
        audit = MagicMock()

        _run([cfg], MagicMock(return_value=[opp]), [opp], audit)

        audit.log.assert_called()
        assert audit.log.call_args[0][0] == "scan_completed"


# -- run_scan: report counts -------------------------------------------------

class TestRunScanReport:
    """run_scan returns a ScanReport with correct counts."""

    def test_report_counts_match(self) -> None:
        cfg = _make_config(niche="tax")
        opps = [_make_opportunity(), _make_opportunity()]

        report = _run([cfg], MagicMock(return_value=opps), opps)

        assert isinstance(report, ScanReport)
        assert report.total_drafted == 2
        assert len(report.niches) == 1
        assert report.niches[0].niche == "tax"
        assert report.niches[0].drafted == 2

    def test_report_multiple_niches(self) -> None:
        cfg1 = _make_config(slug="a", niche="tax")
        cfg2 = _make_config(slug="b", niche="parking")
        tax_opps = [_make_opportunity(niche="tax")]
        parking_opps = [
            _make_opportunity(niche="parking"),
            _make_opportunity(niche="parking"),
        ]
        pipeline = MagicMock(side_effect=[tax_opps, parking_opps])
        all_opps = tax_opps + parking_opps

        report = _run([cfg1, cfg2], pipeline, all_opps)

        assert len(report.niches) == 2
        assert report.total_drafted == 3

    def test_empty_configs_returns_empty_report(self) -> None:
        report = _run([], MagicMock())

        assert isinstance(report, ScanReport)
        assert report.total_drafted == 0
        assert report.niches == []


# -- contract tests -----------------------------------------------------------

class TestScanReportContract:
    """ScanReport and NicheReport contract fields match spec."""

    def test_scan_report_fields(self) -> None:
        expected = {
            "niches", "total_candidates", "total_scored",
            "total_drafted", "total_delivered",
        }
        assert set(ScanReport.model_fields.keys()) == expected

    def test_niche_report_fields(self) -> None:
        expected = {
            "niche", "candidates_found", "scored",
            "drafted", "delivered",
        }
        assert set(NicheReport.model_fields.keys()) == expected
