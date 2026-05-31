"""End-to-end integration: scan pipeline -> API (TEST-001).

Validates the full producer/consumer chain:
  run_scan (JOB-001) -> pipeline (PIPE-001) -> dedup (FILT-001)
  -> opportunities table -> GET /api/v1/opportunities (API-001)

Only true external boundaries are stubbed: search provider,
Anthropic SDK, and SMTP/Slack transports. All internal modules
(dedup, keyword filter, config loader, audit, metrics, ORM)
run for real against an in-memory SQLite database.
"""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.jobs.scan import run_scan
from src.backend.services.auth.audit_service import AuditService
from src.backend.services.observability.metrics import MetricsRecorder
from src.backend.services.pipeline.runner import PipelineDeps, run_pipeline

from .conftest import _FakeSettings

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def _run_scan_with_deps(
    session: Session,
    deps: PipelineDeps,
    settings: _FakeSettings,
) -> None:
    """Execute run_scan with injected pipeline deps."""
    audit = AuditService(session)
    metrics = MetricsRecorder(session)

    def _pipeline_fn(
        config: object, session: Session,
    ) -> list:
        return run_pipeline(config=config, deps=deps, session=session)

    run_scan(
        config_dir=CONFIG_DIR,
        pipeline_fn=_pipeline_fn,
        session=session,
        settings=settings,
        audit_service=audit,
        metrics_recorder=metrics,
    )
    session.commit()


def test_scan_produces_opportunities_visible_via_api(
    integration_session: Session,
    fake_pipeline_deps: PipelineDeps,
    fake_settings: _FakeSettings,
    integration_client: TestClient,
) -> None:
    """Anti-silo: producer (scan) creates data, consumer (API) sees it.

    Runs the full scan pipeline against both example configs, then
    asserts that GET /api/v1/opportunities returns every opportunity
    the pipeline persisted.
    """
    _run_scan_with_deps(
        integration_session, fake_pipeline_deps, fake_settings,
    )

    resp = integration_client.get("/api/v1/opportunities")
    assert resp.status_code == 200

    opportunities = resp.json()
    assert len(opportunities) > 0, "Scan should produce opportunities"

    urls_from_api = {opp["url"] for opp in opportunities}
    assert len(urls_from_api) == len(opportunities), (
        "Each opportunity should have a unique URL"
    )

    for opp in opportunities:
        assert opp["status"] in ("new", "delivered")
        assert opp["relevance_score"] >= 0.5
        assert opp["draft_reply"]
        assert opp["url"].startswith("https://")


def test_rescan_same_urls_produces_no_duplicates(
    integration_session: Session,
    fake_pipeline_deps: PipelineDeps,
    fake_settings: _FakeSettings,
    integration_client: TestClient,
) -> None:
    """Dedup end-to-end: second scan with same URLs -> zero new rows.

    First scan creates opportunities. Second scan re-discovers the
    same URLs but dedup (FILT-001) filters them out via seen_urls.
    The API must return the same count after both scans.
    """
    _run_scan_with_deps(
        integration_session, fake_pipeline_deps, fake_settings,
    )

    resp1 = integration_client.get("/api/v1/opportunities")
    assert resp1.status_code == 200
    count_after_first = len(resp1.json())
    assert count_after_first > 0

    _run_scan_with_deps(
        integration_session, fake_pipeline_deps, fake_settings,
    )

    resp2 = integration_client.get("/api/v1/opportunities")
    assert resp2.status_code == 200
    count_after_second = len(resp2.json())

    assert count_after_second == count_after_first, (
        f"Dedup failed: had {count_after_first} after first scan, "
        f"got {count_after_second} after second scan"
    )


def test_act_via_api_transitions_status(
    integration_session: Session,
    fake_pipeline_deps: PipelineDeps,
    fake_settings: _FakeSettings,
    integration_client: TestClient,
) -> None:
    """Act endpoint transitions status and re-fetch reflects change."""
    _run_scan_with_deps(
        integration_session, fake_pipeline_deps, fake_settings,
    )

    resp = integration_client.get("/api/v1/opportunities")
    assert resp.status_code == 200
    opportunities = resp.json()
    assert len(opportunities) > 0

    target = opportunities[0]
    opp_id = target["id"]

    act_resp = integration_client.post(
        f"/api/v1/opportunities/{opp_id}/act",
    )
    assert act_resp.status_code == 200
    assert act_resp.json()["status"] == "acted"

    refetch = integration_client.get("/api/v1/opportunities")
    refetched = {o["id"]: o for o in refetch.json()}
    assert refetched[opp_id]["status"] == "acted"


def test_skip_via_api_transitions_status(
    integration_session: Session,
    fake_pipeline_deps: PipelineDeps,
    fake_settings: _FakeSettings,
    integration_client: TestClient,
) -> None:
    """Skip endpoint transitions status and re-fetch reflects change."""
    _run_scan_with_deps(
        integration_session, fake_pipeline_deps, fake_settings,
    )

    resp = integration_client.get("/api/v1/opportunities")
    assert resp.status_code == 200
    opportunities = resp.json()
    assert len(opportunities) > 0

    target = opportunities[0]
    opp_id = target["id"]

    skip_resp = integration_client.post(
        f"/api/v1/opportunities/{opp_id}/skip",
    )
    assert skip_resp.status_code == 200
    assert skip_resp.json()["status"] == "skipped"

    refetch = integration_client.get("/api/v1/opportunities")
    refetched = {o["id"]: o for o in refetch.json()}
    assert refetched[opp_id]["status"] == "skipped"


def test_niche_filter_returns_correct_subset(
    integration_session: Session,
    fake_pipeline_deps: PipelineDeps,
    fake_settings: _FakeSettings,
    integration_client: TestClient,
) -> None:
    """API niche filter returns only matching opportunities."""
    _run_scan_with_deps(
        integration_session, fake_pipeline_deps, fake_settings,
    )

    resp_all = integration_client.get("/api/v1/opportunities")
    all_opps = resp_all.json()
    niches = {opp["niche"] for opp in all_opps}

    for niche in niches:
        resp = integration_client.get(
            "/api/v1/opportunities", params={"niche": niche},
        )
        assert resp.status_code == 200
        filtered = resp.json()
        assert all(o["niche"] == niche for o in filtered)
        assert len(filtered) > 0


def test_scan_records_audit_logs(
    integration_session: Session,
    fake_pipeline_deps: PipelineDeps,
    fake_settings: _FakeSettings,
) -> None:
    """Scan pipeline records audit events for generated opportunities."""
    from src.backend.models.audit_log import AuditLog

    _run_scan_with_deps(
        integration_session, fake_pipeline_deps, fake_settings,
    )

    audit_rows = integration_session.query(AuditLog).all()
    actions = {row.action for row in audit_rows}

    assert "opportunity_generated" in actions
    assert "scan_completed" in actions


def test_scan_marks_urls_as_seen(
    integration_session: Session,
    fake_pipeline_deps: PipelineDeps,
    fake_settings: _FakeSettings,
) -> None:
    """Pipeline marks processed URLs in seen_urls for dedup."""
    from src.backend.models.seen_url import SeenUrl

    _run_scan_with_deps(
        integration_session, fake_pipeline_deps, fake_settings,
    )

    seen_rows = integration_session.query(SeenUrl).all()
    assert len(seen_rows) > 0

    seen_urls = {row.url for row in seen_rows}
    for row in seen_rows:
        assert row.niche
        assert row.url in seen_urls
