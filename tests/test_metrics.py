"""Tests for the observability metrics service (OBSERV-001).

Covers: recording metrics, daily stats aggregation, and DB failure
resilience. Uses an in-memory SQLite session from conftest.
"""

import logging
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from contracts.observability.metrics import MetricsData
from src.backend.models.metric import Metric
from src.backend.services.observability.metrics import MetricsRecorder


class TestRecordMetric:
    """MetricsRecorder.record() writes to the Metric table."""

    def test_record_inserts_row(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record("searches_run", 5.0, "tax")

        rows = db_session.query(Metric).all()
        assert len(rows) == 1
        assert rows[0].metric_name == "searches_run"
        assert rows[0].value == 5.0
        assert rows[0].niche == "tax"

    def test_record_multiple_metrics(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record("searches_run", 3.0, "tax")
        recorder.record("candidates_found", 12.0, "tax")

        rows = db_session.query(Metric).all()
        assert len(rows) == 2

    def test_record_db_failure_does_not_raise(
        self, db_session: Session,
    ) -> None:
        recorder = MetricsRecorder(db_session)
        with patch.object(
            db_session, "commit", side_effect=Exception("DB down"),
        ):
            recorder.record("searches_run", 5.0, "tax")

    def test_record_db_failure_logs_error(
        self, db_session: Session, caplog: pytest.LogCaptureFixture,
    ) -> None:
        recorder = MetricsRecorder(db_session)
        with (
            patch.object(
                db_session, "commit", side_effect=Exception("DB down"),
            ),
            caplog.at_level(logging.ERROR),
        ):
            recorder.record("searches_run", 5.0, "tax")

        assert any("METRIC_RECORD_FAILED" in r.message for r in caplog.records)


class TestRecordSearchRun:
    """MetricsRecorder.record_search_run() convenience method."""

    def test_records_two_metrics(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record_search_run("parking", candidates_found=8, queries_run=3)

        rows = db_session.query(Metric).all()
        names = {r.metric_name for r in rows}
        assert "candidates_found" in names
        assert "queries_run" in names

    def test_values_match(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record_search_run("parking", candidates_found=8, queries_run=3)

        rows = db_session.query(Metric).all()
        by_name = {r.metric_name: r.value for r in rows}
        assert by_name["candidates_found"] == 8.0
        assert by_name["queries_run"] == 3.0

    def test_niche_is_set(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record_search_run("parking", candidates_found=1, queries_run=1)

        rows = db_session.query(Metric).all()
        assert all(r.niche == "parking" for r in rows)


class TestRecordAiTokens:
    """MetricsRecorder.record_ai_tokens() convenience method."""

    def test_records_three_metrics(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record_ai_tokens(
            niche="tax",
            model="haiku",
            input_tokens=500,
            output_tokens=200,
            cost_usd=0.003,
        )

        rows = db_session.query(Metric).all()
        names = {r.metric_name for r in rows}
        assert "ai_input_tokens_haiku" in names
        assert "ai_output_tokens_haiku" in names
        assert "ai_cost_usd" in names

    def test_token_values(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record_ai_tokens(
            niche="tax",
            model="sonnet",
            input_tokens=1000,
            output_tokens=400,
            cost_usd=0.01,
        )

        rows = db_session.query(Metric).all()
        by_name = {r.metric_name: r.value for r in rows}
        assert by_name["ai_input_tokens_sonnet"] == 1000.0
        assert by_name["ai_output_tokens_sonnet"] == 400.0
        assert by_name["ai_cost_usd"] == pytest.approx(0.01)


class TestRecordDelivery:
    """MetricsRecorder.record_delivery() convenience method."""

    def test_records_delivery_metrics(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record_delivery(
            niche="parking", opportunities_sent=5, success=True,
        )

        rows = db_session.query(Metric).all()
        names = {r.metric_name for r in rows}
        assert "delivery_sent" in names
        assert "delivery_success" in names

    def test_success_flag_value(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record_delivery(niche="tax", opportunities_sent=3, success=True)

        rows = db_session.query(Metric).all()
        by_name = {r.metric_name: r.value for r in rows}
        assert by_name["delivery_success"] == 1.0

    def test_failure_flag_value(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record_delivery(niche="tax", opportunities_sent=3, success=False)

        rows = db_session.query(Metric).all()
        by_name = {r.metric_name: r.value for r in rows}
        assert by_name["delivery_success"] == 0.0


class TestGetDailyStats:
    """MetricsRecorder.get_daily_stats() aggregation."""

    def test_empty_returns_empty_dict(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        stats = recorder.get_daily_stats()
        assert stats == {}

    def test_aggregates_by_niche(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record("candidates_found", 5.0, "tax")
        recorder.record("candidates_found", 3.0, "tax")
        recorder.record("candidates_found", 10.0, "parking")

        stats = recorder.get_daily_stats()
        assert "tax" in stats
        assert "parking" in stats
        assert stats["tax"]["candidates_found"]["sum"] == pytest.approx(8.0)
        assert stats["tax"]["candidates_found"]["count"] == 2
        assert stats["parking"]["candidates_found"]["sum"] == pytest.approx(10.0)

    def test_filter_by_niche(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record("candidates_found", 5.0, "tax")
        recorder.record("candidates_found", 10.0, "parking")

        stats = recorder.get_daily_stats(niche="tax")
        assert "tax" in stats
        assert "parking" not in stats

    def test_avg_calculation(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record("ai_cost_usd", 0.01, "tax")
        recorder.record("ai_cost_usd", 0.03, "tax")

        stats = recorder.get_daily_stats(niche="tax")
        assert stats["tax"]["ai_cost_usd"]["avg"] == pytest.approx(0.02)

    def test_ignores_old_metrics(self, db_session: Session) -> None:
        recorder = MetricsRecorder(db_session)
        recorder.record("candidates_found", 5.0, "tax")

        old = db_session.query(Metric).first()
        old.timestamp = datetime(2020, 1, 1, tzinfo=UTC)
        db_session.commit()

        stats = recorder.get_daily_stats()
        assert stats == {}


class TestMetricsDataContract:
    """Contract DTO can be constructed from daily stats."""

    def test_metrics_data_from_stats(self) -> None:
        data = MetricsData(
            niche="tax",
            period="daily",
            metrics={
                "candidates_found": {"sum": 8.0, "count": 2, "avg": 4.0},
            },
        )
        assert data.niche == "tax"
        assert data.metrics["candidates_found"]["sum"] == 8.0

    def test_metrics_data_serializes(self) -> None:
        data = MetricsData(
            niche="tax",
            period="daily",
            metrics={},
        )
        dumped = data.model_dump()
        assert "niche" in dumped
        assert "period" in dumped
        assert "metrics" in dumped
