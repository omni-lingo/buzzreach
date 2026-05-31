/**
 * Opportunity detail page with draft editing (FEAT-001).
 *
 * Shows the full opportunity context and integrates the DraftEditor
 * for inline editing, version toggling, save/discard, and regeneration.
 * Pencil icon toggles between read-only and edit modes.
 */

import React, { useCallback, useEffect, useState } from "react";

import DraftEditor from "../components/DraftEditor";
import type { DraftResponse, Opportunity } from "../components/opportunityApi";

interface OpportunityDetailProps {
  opportunityId: string;
}

const API_BASE = "/api/v1";

async function fetchOpportunity(id: string): Promise<Opportunity> {
  const res = await fetch(`${API_BASE}/opportunities/${id}`);
  if (!res.ok) throw new Error("Failed to load opportunity");
  return res.json();
}

const OpportunityDetail: React.FC<OpportunityDetailProps> = ({
  opportunityId,
}) => {
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOpportunity = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const opp = await fetchOpportunity(opportunityId);
      setOpportunity(opp);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Load failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [opportunityId]);

  useEffect(() => {
    loadOpportunity();
  }, [loadOpportunity]);

  const handleDraftChange = useCallback(
    (draft: DraftResponse) => {
      if (!opportunity) return;
      setOpportunity({
        ...opportunity,
        draft_reply: draft.original_draft,
        edited_draft: draft.edited_draft,
      });
    },
    [opportunity]
  );

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error-banner">{error}</div>;
  if (!opportunity) return <div className="error-banner">Not found</div>;

  const currentDraft =
    opportunity.edited_draft ?? opportunity.draft_reply;

  return (
    <div className="opportunity-detail">
      <DetailHeader opportunity={opportunity} />
      <DetailContext opportunity={opportunity} />

      <div className="draft-section">
        <div className="draft-section-header">
          <h3>Draft Reply</h3>
          <button
            onClick={() => setEditing(!editing)}
            className="edit-toggle-btn"
            title={editing ? "Close editor" : "Edit draft"}
            aria-label={editing ? "Close editor" : "Edit draft"}
          >
            {editing ? "Close" : "Edit"}
          </button>
        </div>

        {editing ? (
          <DraftEditor
            opportunityId={opportunity.id}
            originalDraft={opportunity.draft_reply}
            editedDraft={opportunity.edited_draft}
            onDraftChange={handleDraftChange}
          />
        ) : (
          <DraftReadOnly text={currentDraft} />
        )}
      </div>
    </div>
  );
};

interface DetailHeaderProps {
  opportunity: Opportunity;
}

const DetailHeader: React.FC<DetailHeaderProps> = ({ opportunity }) => (
  <div className="detail-header">
    <h2>
      <a
        href={opportunity.url}
        target="_blank"
        rel="noopener noreferrer"
      >
        {opportunity.title}
      </a>
    </h2>
    <div className="detail-meta">
      <span className="detail-source">{opportunity.source}</span>
      <span className="detail-niche">{opportunity.niche}</span>
      <span className="detail-score">
        {(opportunity.relevance_score * 100).toFixed(0)}% match
      </span>
      <span className={`detail-status status-${opportunity.status}`}>
        {opportunity.status}
      </span>
    </div>
  </div>
);

interface DetailContextProps {
  opportunity: Opportunity;
}

const DetailContext: React.FC<DetailContextProps> = ({ opportunity }) => (
  <div className="detail-context">
    <h3>Why Matched</h3>
    <p>{opportunity.why_matched}</p>
  </div>
);

interface DraftReadOnlyProps {
  text: string;
}

const DraftReadOnly: React.FC<DraftReadOnlyProps> = ({ text }) => (
  <div className="draft-readonly">
    <pre>{text}</pre>
    <div className="draft-counts">
      <span>{text.trim() ? text.trim().split(/\s+/).length : 0} words</span>
      <span>{text.length} characters</span>
    </div>
  </div>
);

export default OpportunityDetail;
