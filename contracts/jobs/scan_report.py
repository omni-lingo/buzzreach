"""Cross-module contract for scan job results (JOB-001).

This DTO is the boundary contract between the jobs module and any
consumers that need scan run summaries (logs, monitoring, dashboards).
"""

from pydantic import BaseModel, Field


class NicheReport(BaseModel):
    """Per-niche breakdown of a scan run.

    Attributes:
        niche: The product niche scanned.
        candidates_found: Raw candidates returned by the pipeline.
        scored: Candidates that passed relevance scoring.
        drafted: Opportunities with draft replies generated.
        delivered: Opportunities included in the digest.
    """

    niche: str
    candidates_found: int = Field(ge=0)
    scored: int = Field(ge=0)
    drafted: int = Field(ge=0)
    delivered: int = Field(ge=0)


class ScanReport(BaseModel):
    """Summary of a complete scan run across all product configs.

    Attributes:
        niches: Per-niche breakdown of results.
        total_candidates: Sum of candidates across all niches.
        total_scored: Sum of scored across all niches.
        total_drafted: Sum of drafted across all niches.
        total_delivered: Sum of delivered across all niches.
    """

    niches: list[NicheReport] = Field(default_factory=list)
    total_candidates: int = Field(ge=0, default=0)
    total_scored: int = Field(ge=0, default=0)
    total_drafted: int = Field(ge=0, default=0)
    total_delivered: int = Field(ge=0, default=0)
