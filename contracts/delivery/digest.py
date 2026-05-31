"""Cross-module contract for Digest data.

This DTO is the boundary contract between the delivery module (DELIV-001
builds the digest) and its consumers: DELIV-002 (sends the digest) and
JOB-001 (orchestrates fetch + build + send). Changing this file breaks
those modules at import time.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class Digest(BaseModel):
    """A ready-to-send digest containing rendered opportunity summaries.

    Attributes:
        subject: Email subject line.
        text_body: Plain-text version of the digest.
        html_body: HTML version of the digest.
        opportunity_ids: UUIDs of opportunities included in this digest.
    """

    subject: str
    text_body: str
    html_body: str
    opportunity_ids: list[UUID] = Field(default_factory=list)
