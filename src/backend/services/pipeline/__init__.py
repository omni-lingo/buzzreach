"""Pipeline orchestrator module (PIPE-001).

Exports ``run_pipeline`` and ``PipelineDeps`` for use by JOB-001.
"""

from src.backend.services.pipeline.runner import PipelineDeps, run_pipeline

__all__ = ["PipelineDeps", "run_pipeline"]
