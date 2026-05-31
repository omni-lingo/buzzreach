/**
 * Opportunity card with action tracking (FEAT-003).
 *
 * Displays an opportunity with draft reply and action buttons.
 * "Paste & Open" pops up a form to optionally paste the reply URL.
 * Auto-logs "posted" action with optional reply URL.
 * Shows action status indicators ("Posted", "Archived", etc.).
 */

import React, { useCallback, useEffect, useState } from "react";

import type { Opportunity, OpportunityAction } from "./opportunityApi";
import { fetchActions, logAction } from "./opportunityApi";

interface OpportunityCardProps {
  opportunity: Opportunity;
  onStatusChange?: () => void;
}

const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  onStatusChange,
}) => {
  const [actions, setActions] = useState<OpportunityAction[]>([]);
  const [showPostForm, setShowPostForm] = useState(false);
  const [replyUrl, setReplyUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const latestAction = actions.length > 0
    ? actions[actions.length - 1]
    : null;

  const loadActions = useCallback((): void => {
    fetchActions(opportunity.id)
      .then(setActions)
      .catch((e: Error) => setError(e.message));
  }, [opportunity.id]);

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
      .then(() => handleAction("copied"))
      .catch((e: Error) => setError(e.message));
  };

  return (
    <div className="opportunity-card">
      <CardHeader
        opportunity={opportunity}
        latestAction={latestAction}
      />

      <p className="opp-why">{opportunity.why_matched}</p>

      <div className="opp-draft">
        <h4>Draft Reply</h4>
        <pre>{opportunity.draft_reply}</pre>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <CardActions
        loading={loading}
        showPostForm={showPostForm}
        onView={() => handleAction("viewed")}
        onCopy={handleCopy}
        onOpenPostForm={() => setShowPostForm(true)}
        onArchive={() => handleAction("archived")}
      />

      {showPostForm && (
        <PostUrlForm
          replyUrl={replyUrl}
          setReplyUrl={setReplyUrl}
          onSubmit={handlePostSubmit}
          onCancel={() => setShowPostForm(false)}
          loading={loading}
        />
      )}

      <ActionHistory actions={actions} />
    </div>
  );
};

interface CardHeaderProps {
  opportunity: Opportunity;
  latestAction: OpportunityAction | null;
}

const CardHeader: React.FC<CardHeaderProps> = ({
  opportunity,
  latestAction,
}) => (
  <div className="opp-header">
    <h3>
      <a
        href={opportunity.url}
        target="_blank"
        rel="noopener noreferrer"
      >
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

interface StatusBadgeProps {
  actionType: string;
}

const STATUS_LABELS: Record<string, string> = {
  viewed: "Viewed",
  copied: "Copied",
  posted: "Posted",
  archived: "Archived",
};

const StatusBadge: React.FC<StatusBadgeProps> = ({ actionType }) => (
  <span className={`status-badge status-${actionType}`}>
    {STATUS_LABELS[actionType] ?? actionType}
  </span>
);

interface CardActionsProps {
  loading: boolean;
  showPostForm: boolean;
  onView: () => void;
  onCopy: () => void;
  onOpenPostForm: () => void;
  onArchive: () => void;
}

const CardActions: React.FC<CardActionsProps> = ({
  loading,
  showPostForm,
  onView,
  onCopy,
  onOpenPostForm,
  onArchive,
}) => (
  <div className="opp-actions">
    <button onClick={onView} disabled={loading}>
      Mark Viewed
    </button>
    <button onClick={onCopy} disabled={loading}>
      Copy Draft
    </button>
    <button
      onClick={onOpenPostForm}
      disabled={loading || showPostForm}
      className="post-btn"
    >
      Paste &amp; Open
    </button>
    <button
      onClick={onArchive}
      disabled={loading}
      className="archive-btn"
    >
      Archive
    </button>
  </div>
);

interface PostUrlFormProps {
  replyUrl: string;
  setReplyUrl: (v: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  loading: boolean;
}

const PostUrlForm: React.FC<PostUrlFormProps> = ({
  replyUrl,
  setReplyUrl,
  onSubmit,
  onCancel,
  loading,
}) => (
  <div className="post-url-form">
    <label>
      Reply URL (optional)
      <input
        type="url"
        value={replyUrl}
        onChange={(e) => setReplyUrl(e.target.value)}
        placeholder="https://reddit.com/r/.../comment/..."
      />
    </label>
    <div className="post-url-actions">
      <button onClick={onSubmit} disabled={loading}>
        Log as Posted
      </button>
      <button onClick={onCancel} disabled={loading}>
        Cancel
      </button>
    </div>
  </div>
);

interface ActionHistoryProps {
  actions: OpportunityAction[];
}

const ActionHistory: React.FC<ActionHistoryProps> = ({ actions }) => {
  if (actions.length === 0) return null;

  return (
    <details className="action-history">
      <summary>Action History ({actions.length})</summary>
      <ul>
        {actions.map((a) => (
          <li key={a.id}>
            <span className="action-type">{a.action_type}</span>
            <span className="action-time">
              {new Date(a.created_at).toLocaleString()}
            </span>
            {a.posted_url && (
              <a
                href={a.posted_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                View Reply
              </a>
            )}
          </li>
        ))}
      </ul>
    </details>
  );
};

export default OpportunityCard;
