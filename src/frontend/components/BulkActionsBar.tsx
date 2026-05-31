/**
 * Bulk actions toolbar (FEAT-006).
 *
 * Shows when items are selected: "X selected" + action buttons.
 * Actions: Archive, Regenerate, Export CSV, Delete.
 * Confirmation modal for destructive actions (delete).
 * Toast notification after bulk action completes.
 */

import React, { useCallback, useState } from "react";

import {
  bulkArchive,
  bulkDelete,
  bulkExportCsv,
  bulkRegenerate,
} from "./bulkApi";

interface BulkActionsBarProps {
  selectedIds: Set<string>;
  onComplete: () => void;
  onDeselectAll: () => void;
}

interface ToastState {
  message: string;
  type: "success" | "error";
}

const BulkActionsBar: React.FC<BulkActionsBarProps> = ({
  selectedIds,
  onComplete,
  onDeselectAll,
}) => {
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const count = selectedIds.size;
  if (count === 0) return null;

  const ids = Array.from(selectedIds);

  const showToast = (message: string, type: "success" | "error"): void => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleArchive = (): void => {
    setLoading(true);
    bulkArchive(ids)
      .then((r) => {
        showToast(`Archived ${r.processed} opportunities`, "success");
        onDeselectAll();
        onComplete();
      })
      .catch((e: Error) => showToast(e.message, "error"))
      .finally(() => setLoading(false));
  };

  const handleRegenerate = (): void => {
    setLoading(true);
    bulkRegenerate(ids)
      .then((r) => {
        showToast(`Regenerating ${r.processed} drafts`, "success");
        onDeselectAll();
        onComplete();
      })
      .catch((e: Error) => showToast(e.message, "error"))
      .finally(() => setLoading(false));
  };

  const handleExport = (): void => {
    setLoading(true);
    bulkExportCsv(ids)
      .then(() => {
        showToast(`Exported ${count} opportunities to CSV`, "success");
      })
      .catch((e: Error) => showToast(e.message, "error"))
      .finally(() => setLoading(false));
  };

  const handleDeleteConfirm = (): void => {
    setShowDeleteConfirm(false);
    setLoading(true);
    bulkDelete(ids)
      .then((r) => {
        showToast(`Deleted ${r.processed} opportunities`, "success");
        onDeselectAll();
        onComplete();
      })
      .catch((e: Error) => showToast(e.message, "error"))
      .finally(() => setLoading(false));
  };

  return (
    <>
      <div className="bulk-actions-bar" role="toolbar">
        <span className="bulk-count">{count} selected</span>

        <BulkButton
          label="Archive"
          onClick={handleArchive}
          disabled={loading}
          className="bulk-btn-archive"
        />
        <BulkButton
          label="Regenerate"
          onClick={handleRegenerate}
          disabled={loading}
          className="bulk-btn-regenerate"
        />
        <BulkButton
          label="Export CSV"
          onClick={handleExport}
          disabled={loading}
          className="bulk-btn-export"
        />
        <BulkButton
          label="Delete"
          onClick={() => setShowDeleteConfirm(true)}
          disabled={loading}
          className="bulk-btn-delete"
        />
        <BulkButton
          label="Deselect All"
          onClick={onDeselectAll}
          disabled={loading}
          className="bulk-btn-deselect"
        />
      </div>

      {showDeleteConfirm && (
        <ConfirmModal
          count={count}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setShowDeleteConfirm(false)}
        />
      )}

      {toast && <Toast message={toast.message} type={toast.type} />}
    </>
  );
};

interface BulkButtonProps {
  label: string;
  onClick: () => void;
  disabled: boolean;
  className: string;
}

const BulkButton: React.FC<BulkButtonProps> = ({
  label,
  onClick,
  disabled,
  className,
}) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={className}
  >
    {label}
  </button>
);

interface ConfirmModalProps {
  count: number;
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
  count,
  onConfirm,
  onCancel,
}) => (
  <div className="bulk-confirm-overlay" role="dialog">
    <div className="bulk-confirm-modal">
      <h3>Confirm Delete</h3>
      <p>
        Are you sure you want to delete {count} opportunit
        {count === 1 ? "y" : "ies"}? This action can be recovered.
      </p>
      <div className="bulk-confirm-actions">
        <button onClick={onConfirm} className="bulk-btn-danger">
          Delete
        </button>
        <button onClick={onCancel}>Cancel</button>
      </div>
    </div>
  </div>
);

interface ToastProps {
  message: string;
  type: "success" | "error";
}

const Toast: React.FC<ToastProps> = ({ message, type }) => (
  <div className={`bulk-toast bulk-toast-${type}`} role="alert">
    {message}
  </div>
);

export default BulkActionsBar;
