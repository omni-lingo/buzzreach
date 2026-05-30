"""Cross-module contract for AI relevance scoring (AI-002).

This DTO is the boundary contract between the AI scorer and consumers:
PIPE-001 (pipeline stage 4 gate) decides whether to proceed to drafting
based on ``is_seeking_help``, ``angle_already_covered``, and ``score``.
"""

from pydantic import BaseModel, Field


class RelevanceResult(BaseModel):
    """Structured verdict from the Haiku relevance scorer.

    Attributes:
        score: Relevance score clamped to [0, 1].
        is_seeking_help: Whether the post author is asking for help.
        angle_already_covered: Whether existing comments already cover
            the product's angle.
        reason: Short explanation of the verdict for audit/debug.
    """

    score: float = Field(ge=0.0, le=1.0)
    is_seeking_help: bool
    angle_already_covered: bool
    reason: str
