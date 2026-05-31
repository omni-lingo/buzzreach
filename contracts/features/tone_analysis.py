"""Cross-module contract for tone analysis results (FEAT-005).

Consumed by:
- FEAT-005 (tone detector service)
- FEAT-001 (draft editor shows tone metrics)
- AI-002 (scorer uses as quality signal)
- API-001 (tone analysis endpoints)
"""

from pydantic import BaseModel, Field


class ToneWarning(BaseModel):
    """A single tone warning with a code and user-facing message."""

    code: str
    message: str
    suggestion: str


class ToneMetrics(BaseModel):
    """Tone analysis results for a piece of draft text.

    Attributes:
        reading_level: Flesch-Kincaid grade level (6-16+ scale).
        marketing_score: 0-1, how salesy the text sounds.
        ai_likelihood: 0-1, probability the text was AI-written.
        authenticity_score: 0-1, human-like quality.
        warnings: List of actionable warnings.
    """

    reading_level: float = Field(ge=0.0)
    marketing_score: float = Field(ge=0.0, le=1.0)
    ai_likelihood: float = Field(ge=0.0, le=1.0)
    authenticity_score: float = Field(ge=0.0, le=1.0)
    warnings: list[ToneWarning] = Field(default_factory=list)
