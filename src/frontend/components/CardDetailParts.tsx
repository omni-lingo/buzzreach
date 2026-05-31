/**
 * Detail-mode sub-components for OpportunityCard (FEAT-003).
 *
 * PostUrlForm: URL input for logging a "posted" action.
 * ActionHistory: Collapsible timeline of past actions.
 */

import React from "react";

import type { OpportunityAction } from "./opportunityApi";

// --------------- PostUrlForm ---------------

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

// --------------- ActionHistory ---------------

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

export { ActionHistory, PostUrlForm };
