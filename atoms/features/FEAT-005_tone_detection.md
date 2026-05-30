# ATOM: FEAT-005 — Tone Detection & Quality Scoring

**Layer:** L2
**Module:** features
**Effort:** M
**Depends on:** AI-003

## Inputs (what this atom reads/consumes)
- Generated draft text (AI-003)
- Community platform (Reddit, Quora, etc.)

## Outputs (what this atom produces)
- `src/backend/services/tone_detector.py`:
  - `analyze_tone(draft_text)` → returns tone metrics
  - Metrics: { reading_level, marketing_score, ai_likelihood, authenticity_score }
  - `reading_level` — Flesch-Kincaid (6-16+ scale)
  - `marketing_score` — 0-1, how "salesy" the text is (0 = conversational, 1 = heavy sell)
  - `ai_likelihood` — 0-1, probability text was AI-written (based on patterns)
  - `authenticity_score` — 0-1, human-like quality (inverse of ai_likelihood)
- Warnings:
  - If `marketing_score > 0.7` → "Draft sounds like advertisement, community may reject"
  - If `ai_likelihood > 0.8` → "Draft may be detected as AI, consider editing"
  - If `reading_level > 12` → "Dense text, simplify for accessibility"
- `src/frontend/components/ToneIndicator.tsx` — visual feedback:
  - Gauge/progress bar for each metric
  - Warning icons (red) if problematic
  - "Edit to improve tone" suggestions
- Integrated into FEAT-001 (draft editor):
  - Show tone metrics while editing
  - Update in real-time as user types
- `tests/test_tone_detection.py` — analyze various draft styles

## Acceptance criteria
- [ ] Reading level calculated accurately (test against samples)
- [ ] Marketing score detects salesy language (keywords: "buy", "limited", "now", etc.)
- [ ] AI likelihood score trained on known AI-written text
- [ ] Authenticity score helpful for user (actionable feedback)
- [ ] Tone analysis fast (<200ms per draft)
- [ ] Visual indicators clear (user understands warnings)
- [ ] Suggestions for improvement provided
- [ ] No false positives (don't flag legitimate business mentions)

## Cross-module contracts
- Integrates into draft generation (AI-003)
- Displayed in draft editor (FEAT-001)
- Used by AI-002 as quality signal for scoring
