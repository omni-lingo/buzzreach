"""Cross-module contract for extracted page content (EXT-001).

This DTO is the boundary contract between the extraction module and
consumers: AI-002 (scorer), AI-003 (drafter), PIPE-001 (pipeline).
"""

from pydantic import BaseModel, Field


class ExtractedContent(BaseModel):
    """Extracted content from a web page.

    Produced by the content extractor. Consumed by the AI scoring
    and drafting stages to understand the thread context.
    """

    url: str
    title: str
    body: str
    comments: list[str] = Field(default_factory=list)
    truncated: bool = False
