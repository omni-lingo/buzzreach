"""Cross-module contract for search candidates (DISC-002).

A Candidate is a single search result found by the search provider.
Consumed by extraction (EXT-001), filter, and pipeline (PIPE-001).
"""

from datetime import datetime

from pydantic import BaseModel, Field


class Candidate(BaseModel):
    """A search result returned by the search provider.

    Attributes:
        url: Full URL of the discovered page.
        title: Page title from search results.
        snippet: Short text snippet from search results.
        source: Hostname of the URL (e.g. ``reddit.com``).
        found_at: Timestamp when the result was discovered.
    """

    url: str
    title: str
    snippet: str
    source: str = Field(description="Hostname extracted from the URL")
    found_at: datetime = Field(default_factory=datetime.utcnow)
