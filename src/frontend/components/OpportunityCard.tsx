/**
 * Opportunity card with action tracking (FEAT-003, FE-002).
 *
 * Two modes:
 * 1. Detail mode (FEAT-003): action history, post URL form.
 * 2. Dashboard mode (FE-002): copy draft, mark posted, archive
 *    via parent callbacks.
 */

import React, { useCallback, useEffect, useRef, useState } from "react";

import type { Opportunity as ClientOpportunity } from "../api/opportunitiesClient";
import { ActionHistory, PostUrlForm } from "./CardDetailParts";
import type { Opportunity, OpportunityAction } from "./opportunityApi";
import { fetchActions, logAction } from "./opportunityApi";

type CardOpportunity = Opportunity | ClientOpportunity;

interface OpportunityCardProps {
  opportunity: CardOpportunity;
  onStatusChange?: () => void;
  isSelected?: boolean;
  isKeyboardActive?: boolean;
  onToggleSelect?: (id: string) => void;
  onMarkPosted?: (id: string) => void;
  onArchive?: (id: string) => void;
}

const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  onStatusChange,
  isSelected = false,
  isKeyboardActive = false,
  onToggleSelect,
  onMarkPosted,
  onArchive,
}) => {
  const isDashboardMode = !!(onMarkPosted || onArchive);
  const [actions, setActions] = useState<OpportunityAction[]>([]);
  const [showPostForm, setShowPostForm] = useState(false);
  const [replyUrl, setReplyUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isKeyboardActive && cardRef.current) {
      cardRef.current.scrollIntoView({ block: "nearest" });
    }
  }, [isKeyboardActive]);

  const latestAction = actions.length > 0
    ? actions[actions.length - 1]
    : null;

  const loadActions = useCallback((): void => {
    if (isDashboardMode) return;
    fetchActions(opportunity.id)
      .then(setActions)
      .catch((e: Error) => setError(e.message));
  }, [opportunity.id, isDashboardMode]);

  useEffect(() => {
    loadActions();
  }, [loadActions]);

  const handleAction = (actionType: string): void => {
    setError(null);
    setLoading(true);
    logAction(opportunity.id, actionType)
      .then(() => {
        loadActions();
        onStatusChange?.();
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const handlePostSubmit = (): void => {
    setError(null);
    setLoading(true);
    const url = replyUrl.trim() || undefined;
    logAction(opportunity.id, "posted", url)
      .then(() => {
        setShowPostForm(false);
        setReplyUrl("");
        loadActions();
        onStatusChange?.();
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const handleCopy = (): void => {
    navigator.clipboard
      .writeText(opportunity.draft_reply)
      .then(() => {
        if (!isDashboardMode) handleAction("copied");
      })
      .catch((e: Error) => setError(e.message));
  };

  const cardClass = isKeyboardActive
    ? "opportunity-card keyboard-active"
    : "opportunity-card";

  return (
    <div className={cardClass} ref={cardRef}>
      <CardHeader
        opportunity={opportunity}
        latestAction={latestAction}
        isSelected={isSelected}
        onToggleSelect={onToggleSelect}
      />

      <p className="opp-why">{opportunity.why_matched}</p>

      <div className="opp-draft">
        <h4>Draft Reply</h4>
        <pre>{opportunity.draft_reply}</pre>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {isDashboardMode ? (
        <DashboardActions
          loading={loading}
          onCopy={handleCopy}
          onMarkPosted={() => onMarkPosted?.(opportunity.id)}
          onArchive={() => onArchive?.(opportunity.id)}
        />
      ) : (
        <DetailActions
          loading={loading}
          showPostForm={showPostForm}
          onView={() => handleAction("viewed")}
          onCopy={handleCopy}
          onOpenPostForm={() => setShowPostForm(true)}
          onArchive={() => handleAction("archived")}
        />
      )}

      {!isDashboardMode && showPostForm && (
        <PostUrlForm
          replyUrl={replyUrl}
          setReplyUrl={setReplyUrl}
          onSubmit={handlePostSubmit}
          onCancel={() => setShowPostForm(false)}
          loading={loading}
        />
      )}

      {!isDashboardMode && <ActionHistory actions={actions} />}
    </div>
  );
};

// --------------- Sub-components ---------------

interface CardHeaderProps {
  opportunity: CardOpportunity;
  latestAction: OpportunityAction | null;
  isSelected: boolean;
  onToggleSelect?: (id: string) => void;
}

const CardHeader: React.FC<CardHeaderProps> = ({
  opportunity,
  latestAction,
  isSelected,
  onToggleSelect,
}) => (
  <div className="opp-header">
    {onToggleSelect && (
      <input
        type="checkbox"
        className="opp-select-checkbox"
        checked={isSelected}
        onChange={() => onToggleSelect(opportunity.id)}
        aria-label={`Select ${opportunity.title}`}
      />
    )}
    <h3 className="opp-title">
      <a href={opportunity.url} target="_blank" rel="noopener noreferrer">
        {opportunity.title}
      </a>
    </h3>
    <span className="opp-source">{opportunity.source}</span>
    <span className="opp-score">
      {(opportunity.relevance_score * 100).toFixed(0)}%
    </span>
    {latestAction && (
      <StatusBadge actionType={latestAction.action_type} />
    )}
  </div>
);

const STATUS_LABELS: Record<string, string> = {
  viewed: "Viewed",
  copied: "Copied",
  posted: "Posted",
  archived: "Archived",
};

const StatusBadge: React.FC<{ actionType: string }> = ({ actionType }) => (
  <span className={`status-badge status-${actionType}`}>
    {STATUS_LABELS[actionType] ?? actionType}
  </span>
);

interface DashboardActionsProps {
  loading: boolean;
  onCopy: () => void;
  onMarkPosted: () => void;
  onArchive: () => void;
}

const DashboardActions: React.FC<DashboardActionsProps> = ({
  loading, onCopy, onMarkPosted, onArchive,
}) => (
  <div className="opp-actions">
    <button className="btn-copy-draft" onClick={onCopy} disabled={loading}>
      Copy Draft
    </button>
    <button className="btn-mark-posted" onClick={onMarkPosted} disabled={loading}>
      Mark as Posted
    </button>
    <button className="btn-archive" onClick={onArchive} disabled={loading}>
      Archive
    </button>
  </div>
);

interface DetailActionsProps {
  loading: boolean;
  showPostForm: boolean;
  onView: () => void;
  onCopy: () => void;
  onOpenPostForm: () => void;
  onArchive: () => void;
}

const DetailActions: React.FC<DetailActionsProps> = ({
  loading, showPostForm, onView, onCopy, onOpenPostForm, onArchive,
}) => (
  <div className="opp-actions">
    <button onClick={onView} disabled={loading}>Mark Viewed</button>
    <button onClick={onCopy} disabled={loading}>Copy Draft</button>
    <button
      onClick={onOpenPostForm}
      disabled={loading || showPostForm}
      className="post-btn"
    >
      Paste &amp; Open
    </button>
    <button onClick={onArchive} disabled={loading} className="archive-btn">
      Archive
    </button>
  </div>
);

export default OpportunityCard;
