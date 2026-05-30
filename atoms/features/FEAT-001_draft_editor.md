# ATOM: FEAT-001 — Draft Editor & Customization

**Layer:** L4
**Module:** features
**Effort:** M
**Depends on:** FE-002, FEAT-005

## Inputs (what this atom reads/consumes)
- `src/backend/services/draft_generator.py` (AI-003)
- Opportunity model with draft text

## Outputs (what this atom produces)
- `src/frontend/components/DraftEditor.tsx` — rich text editor:
  - Editable draft text (textarea)
  - Inline regenerate button ("Regenerate with different tone")
  - Word count display
  - Character count + platform limits indicator
  - Undo/redo (via keyboard shortcuts)
  - Clear formatting button
- `src/frontend/pages/OpportunityDetail.tsx` — expansion:
  - Show draft + edit option (click pencil icon)
  - Original vs edited version toggle
  - "Save changes" persists to DB
  - "Discard changes" reverts to AI-generated version
- `src/backend/api/opportunities.py` — new routes:
  - PUT `/api/v1/opportunities/{id}/draft` — save edited draft
  - POST `/api/v1/opportunities/{id}/regenerate` — AI re-draft with new tone param
- `src/backend/services/draft_generator.py` — enhancement:
  - `regenerate_draft(opportunity_id, tone_override)` — new tone, same URL context
- UI for tone selection (radio buttons: professional, casual, humorous, technical, etc.)
- `tests/test_draft_editor.py` — save, regenerate, undo/redo

## Acceptance criteria
- [ ] Draft text is editable in text area
- [ ] Changes are saved to DB on "Save" click
- [ ] Original version recoverable (toggle between versions)
- [ ] Regenerate button calls AI with tone param
- [ ] Character count updates as user types
- [ ] Tone options available: at least 5 predefined tones
- [ ] Undo/redo keyboard shortcuts (Ctrl+Z, Ctrl+Shift+Z)
- [ ] Edit history tracked (AUDIT-002) for compliance
- [ ] Changes reflected in copy-to-clipboard
- [ ] Mobile-friendly (keyboard handling)

## Cross-module contracts
- Reads Opportunity (CORE-003)
- Calls AI draft generator (AI-003)
- Updates draft via API-001
- Logs edits (AUDIT-002)
