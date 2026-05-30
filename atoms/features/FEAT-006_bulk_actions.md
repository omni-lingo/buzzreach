# ATOM: FEAT-006 — Bulk Actions (dismiss, regenerate, export)

**Layer:** L4
**Module:** features
**Effort:** S
**Depends on:** FE-002

## Inputs (what this atom reads/consumes)
- Opportunity feed (FE-002)
- User selections

## Outputs (what this atom produces)
- `src/frontend/components/BulkActionsBar.tsx` — toolbar showing when items selected:
  - Checkbox in each card header (for selection)
  - Bottom bar: "X selected" + action buttons
  - Actions: Archive, Regenerate, Export (CSV), Delete
- `src/frontend/hooks/useBulkSelection.ts` — selection state management:
  - `selected` (Set of opportunity IDs)
  - `selectAll()`, `deselectAll()`, `toggle(id)`
- `src/backend/api/opportunities.py` — bulk endpoints:
  - POST `/api/v1/opportunities/bulk/archive` — archive multiple
  - POST `/api/v1/opportunities/bulk/regenerate` — regenerate all selected
  - POST `/api/v1/opportunities/bulk/export` — return CSV
  - DELETE `/api/v1/opportunities/bulk` — delete (soft delete)
- Bulk operations:
  - **Archive**: hide from feed, keep for history
  - **Regenerate**: re-run AI draft for all selected (batch call, cost savings)
  - **Export CSV**: download with columns (URL, Title, Platform, Score, Draft, Action, Date)
  - **Delete**: soft-delete (recoverable, audit logged)
- Confirmation modal for destructive actions (delete)
- Toast notification after bulk action completes
- `tests/test_bulk_actions.tsx` — select, bulk archive, export

## Acceptance criteria
- [ ] Checkboxes selectable on each card
- [ ] Bulk actions bar appears when items selected
- [ ] "Select All" button selects all visible opportunities
- [ ] Archive bulk action removes from feed
- [ ] Regenerate bulk action calls API (batch request)
- [ ] Export CSV includes all relevant columns
- [ ] CSV downloaded with filename: `opportunities_{date}.csv`
- [ ] Confirmation required before delete
- [ ] Toast notification shows success/error
- [ ] Mobile: adapt bulk actions for touch (larger buttons)

## Cross-module contracts
- Uses Opportunity model (CORE-003)
- Calls API endpoints (API-001)
- Integrates into dashboard (FE-002)
