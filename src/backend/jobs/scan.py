"""Scheduled scan job — cron entrypoint (JOB-001).

For each product config: runs the pipeline, accumulates new
opportunities, builds + sends one digest, then logs scan_completed
to the audit table. CLI-invokable as ``python -m src.backend.jobs.scan``.
"""

import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from sqlalchemy.orm import Session

from contracts.config.product_config import ProductConfig
from contracts.jobs.scan_report import NicheReport, ScanReport
from contracts.opportunity.opportunity import OpportunityData
from src.backend.services.config_loader import load_all_configs
from src.backend.services.delivery.digest import (
    build_digest,
    fetch_new_opportunities,
)
from src.backend.services.delivery.sender import send_digest

log = logging.getLogger("buzzreach.jobs.scan")

PipelineFn = Callable[..., list[OpportunityData]]


class _AuditService(Protocol):
    """Subset of AuditService used by the scan job."""

    def log(
        self,
        action: str,
        resource_type: str,
        *,
        change_summary: str | None = None,
    ) -> None: ...


class _MetricsRecorder(Protocol):
    """Subset of MetricsRecorder used by the scan job."""

    def record_delivery(
        self,
        niche: str,
        opportunities_sent: int,
        *,
        success: bool,
    ) -> None: ...


def run_scan(
    config_dir: Path,
    pipeline_fn: PipelineFn,
    session: Session,
    settings: object,
    audit_service: _AuditService,
    metrics_recorder: _MetricsRecorder,
) -> ScanReport:
    """Execute a full scan cycle across all product configs.

    Args:
        config_dir: Directory with per-product JSON config files.
        pipeline_fn: Injected pipeline function (run_pipeline).
        session: SQLAlchemy session for DB operations.
        settings: Application settings for delivery transports.
        audit_service: Audit logger for recording the scan action.
        metrics_recorder: Metrics recorder for delivery tracking.

    Returns:
        A ScanReport summarising per-niche results.
    """
    configs = load_all_configs(config_dir)
    niche_reports = _run_all_pipelines(
        configs, pipeline_fn, session,
    )
    report = _build_report(niche_reports)

    _deliver_digest(session, settings, audit_service, metrics_recorder)
    _audit_scan(audit_service, report, niche_reports)
    _log_summary(report)

    return report


def _run_all_pipelines(
    configs: list[ProductConfig],
    pipeline_fn: PipelineFn,
    session: Session,
) -> list[NicheReport]:
    """Run pipeline for each config, returning per-niche reports."""
    niche_reports: list[NicheReport] = []

    for cfg in configs:
        opps = pipeline_fn(config=cfg, session=session)
        niche_report = NicheReport(
            niche=cfg.niche,
            candidates_found=len(opps),
            scored=len(opps),
            drafted=len(opps),
            delivered=0,
        )
        niche_reports.append(niche_report)
        log.info(
            "Pipeline completed for niche",
            extra={
                "niche": cfg.niche,
                "slug": cfg.slug,
                "drafted": len(opps),
            },
        )

    return niche_reports


def _deliver_digest(
    session: Session,
    settings: object,
    audit_service: _AuditService,
    metrics_recorder: _MetricsRecorder,
) -> None:
    """Fetch new opportunities, build a digest, and send it."""
    opportunities = fetch_new_opportunities(session)
    digest = build_digest(opportunities)
    send_digest(
        digest, settings, audit_service, metrics_recorder, session,
    )


def _audit_scan(
    audit_service: _AuditService,
    report: ScanReport,
    niche_reports: list[NicheReport],
) -> None:
    """Log scan_completed to the audit table with summary."""
    niches_summary = ", ".join(
        f"{nr.niche}: {nr.drafted} drafted"
        for nr in niche_reports
    )
    summary = (
        f"Scan completed. "
        f"Total drafted: {report.total_drafted}, "
        f"delivered: {report.total_delivered}. "
        f"Niches: {niches_summary}"
    )
    audit_service.log(
        "scan_completed",
        "scan",
        change_summary=summary,
    )


def _build_report(niche_reports: list[NicheReport]) -> ScanReport:
    """Aggregate niche reports into a single ScanReport."""
    return ScanReport(
        niches=niche_reports,
        total_candidates=sum(nr.candidates_found for nr in niche_reports),
        total_scored=sum(nr.scored for nr in niche_reports),
        total_drafted=sum(nr.drafted for nr in niche_reports),
        total_delivered=sum(nr.delivered for nr in niche_reports),
    )


def _log_summary(report: ScanReport) -> None:
    """Emit structured log with scan totals."""
    log.info(
        "Scan cycle complete",
        extra={
            "total_candidates": report.total_candidates,
            "total_scored": report.total_scored,
            "total_drafted": report.total_drafted,
            "total_delivered": report.total_delivered,
            "niches_scanned": len(report.niches),
        },
    )


def _cli_main() -> None:
    """CLI entrypoint for ``python -m src.backend.jobs.scan``."""
    from src.backend.db.session import get_session_factory
    from src.backend.logging_config import setup_logging
    from src.backend.services.auth.audit_service import AuditService
    from src.backend.settings import Settings

    setup_logging()
    _settings = Settings()
    _session = get_session_factory()()

    _audit = AuditService(_session)

    # PIPE-001 and OBS-001 provide these; import at call time.
    from src.backend.services.pipeline.runner import run_pipeline  # noqa: PLC0415

    try:
        _report = run_scan(
            config_dir=_settings.config_dir,
            pipeline_fn=run_pipeline,
            session=_session,
            settings=_settings,
            audit_service=_audit,
            metrics_recorder=_build_noop_metrics(),
        )
        log.info(
            "Scan finished",
            extra={"total_drafted": _report.total_drafted},
        )
    except Exception:
        log.error("Scan failed", exc_info=True)
        sys.exit(1)
    finally:
        _session.close()


class _NoopMetrics:
    """Placeholder until OBS-001 provides MetricsRecorder."""

    def record_delivery(
        self,
        niche: str,
        opportunities_sent: int,
        *,
        success: bool,
    ) -> None:
        pass


def _build_noop_metrics() -> _NoopMetrics:
    """Return a no-op metrics recorder for pre-OBS-001 usage."""
    return _NoopMetrics()


if __name__ == "__main__":
    _cli_main()
