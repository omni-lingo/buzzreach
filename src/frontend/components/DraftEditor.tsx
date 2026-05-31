/**
 * Draft Editor component with inline editing (FEAT-001).
 *
 * Features:
 * - Editable textarea for draft text
 * - Word and character count with platform limit indicators
 * - Undo/redo via Ctrl+Z / Ctrl+Shift+Z
 * - Tone selection for regeneration
 * - Save / Discard / Regenerate actions
 */

import React, { useCallback, useEffect, useRef, useState } from "react";

import type { DraftResponse, DraftTone } from "./opportunityApi";
import { discardDraft, regenerateDraft, saveDraft } from "./opportunityApi";

interface DraftEditorProps {
  opportunityId: string;
  originalDraft: string;
  editedDraft: string | null;
  onDraftChange?: (draft: DraftResponse) => void;
}

const TONES: { value: DraftTone; label: string }[] = [
  { value: "professional", label: "Professional" },
  { value: "casual", label: "Casual" },
  { value: "humorous", label: "Humorous" },
  { value: "technical", label: "Technical" },
  { value: "empathetic", label: "Empathetic" },
  { value: "enthusiastic", label: "Enthusiastic" },
];

const PLATFORM_LIMITS: Record<string, number> = {
  Reddit: 10000,
  Twitter: 280,
  LinkedIn: 3000,
  Quora: 5000,
};

const DraftEditor: React.FC<DraftEditorProps> = ({
  opportunityId,
  originalDraft,
  editedDraft,
  onDraftChange,
}) => {
  const [text, setText] = useState(editedDraft ?? originalDraft);
  const [showOriginal, setShowOriginal] = useState(false);
  const [selectedTone, setSelectedTone] = useState<DraftTone>("professional");
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const currentOriginal = useRef(originalDraft);

  useEffect(() => {
    currentOriginal.current = originalDraft;
  }, [originalDraft]);

  const handleTextChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setText(e.target.value);
      setIsDirty(e.target.value !== currentOriginal.current);
    },
    []
  );

  const handleSave = useCallback(async () => {
    setError(null);
    setSaving(true);
    try {
      const result = await saveDraft(opportunityId, text);
      setIsDirty(false);
      onDraftChange?.(result);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Save failed";
      setError(msg);
    } finally {
      setSaving(false);
    }
  }, [opportunityId, text, onDraftChange]);

  const handleDiscard = useCallback(async () => {
    setError(null);
    setSaving(true);
    try {
      const result = await discardDraft(opportunityId);
      setText(result.current_text);
      setIsDirty(false);
      onDraftChange?.(result);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Discard failed";
      setError(msg);
    } finally {
      setSaving(false);
    }
  }, [opportunityId, onDraftChange]);

  const handleRegenerate = useCallback(async () => {
    setError(null);
    setRegenerating(true);
    try {
      const result = await regenerateDraft(opportunityId, selectedTone);
      setText(result.current_text);
      currentOriginal.current = result.original_draft;
      setIsDirty(false);
      onDraftChange?.(result);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Regeneration failed";
      setError(msg);
    } finally {
      setRegenerating(false);
    }
  }, [opportunityId, selectedTone, onDraftChange]);

  const handleCopy = useCallback(() => {
    navigator.clipboard
      .writeText(text)
      .catch(() => setError("Copy to clipboard failed"));
  }, [text]);

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

  return (
    <div className="draft-editor">
      <EditorToolbar
        showOriginal={showOriginal}
        onToggleOriginal={() => setShowOriginal(!showOriginal)}
        onCopy={handleCopy}
        isDirty={isDirty}
      />

      {showOriginal ? (
        <div className="draft-original">
          <h4>Original AI Draft</h4>
          <pre>{currentOriginal.current}</pre>
        </div>
      ) : (
        <textarea
          ref={textareaRef}
          className="draft-textarea"
          value={text}
          onChange={handleTextChange}
          rows={10}
          aria-label="Draft text editor"
        />
      )}

      <CharacterCounts wordCount={wordCount} charCount={charCount} />

      {error && <div className="error-banner">{error}</div>}

      <ToneSelector
        selectedTone={selectedTone}
        onToneChange={setSelectedTone}
        onRegenerate={handleRegenerate}
        regenerating={regenerating}
      />

      <EditorActions
        isDirty={isDirty}
        saving={saving}
        regenerating={regenerating}
        onSave={handleSave}
        onDiscard={handleDiscard}
      />
    </div>
  );
};

interface EditorToolbarProps {
  showOriginal: boolean;
  onToggleOriginal: () => void;
  onCopy: () => void;
  isDirty: boolean;
}

const EditorToolbar: React.FC<EditorToolbarProps> = ({
  showOriginal,
  onToggleOriginal,
  onCopy,
  isDirty,
}) => (
  <div className="draft-toolbar">
    <button
      onClick={onToggleOriginal}
      className="toggle-original-btn"
      title={showOriginal ? "Show edited" : "Show original"}
    >
      {showOriginal ? "Back to Editor" : "View Original"}
    </button>
    <button onClick={onCopy} title="Copy draft to clipboard">
      Copy
    </button>
    {isDirty && <span className="unsaved-indicator">Unsaved changes</span>}
  </div>
);

interface CharacterCountsProps {
  wordCount: number;
  charCount: number;
}

const CharacterCounts: React.FC<CharacterCountsProps> = ({
  wordCount,
  charCount,
}) => (
  <div className="draft-counts">
    <span>{wordCount} words</span>
    <span>{charCount} characters</span>
    {Object.entries(PLATFORM_LIMITS).map(([platform, limit]) => (
      <span
        key={platform}
        className={charCount > limit ? "over-limit" : "within-limit"}
      >
        {platform}: {charCount}/{limit}
      </span>
    ))}
  </div>
);

interface ToneSelectorProps {
  selectedTone: DraftTone;
  onToneChange: (tone: DraftTone) => void;
  onRegenerate: () => void;
  regenerating: boolean;
}

const ToneSelector: React.FC<ToneSelectorProps> = ({
  selectedTone,
  onToneChange,
  onRegenerate,
  regenerating,
}) => (
  <div className="tone-selector">
    <span className="tone-label">Regenerate with tone:</span>
    <div className="tone-options">
      {TONES.map(({ value, label }) => (
        <label key={value} className="tone-radio">
          <input
            type="radio"
            name="draft-tone"
            value={value}
            checked={selectedTone === value}
            onChange={() => onToneChange(value)}
          />
          {label}
        </label>
      ))}
    </div>
    <button
      onClick={onRegenerate}
      disabled={regenerating}
      className="regenerate-btn"
    >
      {regenerating ? "Regenerating..." : "Regenerate"}
    </button>
  </div>
);

interface EditorActionsProps {
  isDirty: boolean;
  saving: boolean;
  regenerating: boolean;
  onSave: () => void;
  onDiscard: () => void;
}

const EditorActions: React.FC<EditorActionsProps> = ({
  isDirty,
  saving,
  regenerating,
  onSave,
  onDiscard,
}) => (
  <div className="draft-actions">
    <button
      onClick={onSave}
      disabled={!isDirty || saving || regenerating}
      className="save-btn"
    >
      {saving ? "Saving..." : "Save Changes"}
    </button>
    <button
      onClick={onDiscard}
      disabled={saving || regenerating}
      className="discard-btn"
    >
      Discard Changes
    </button>
  </div>
);

export default DraftEditor;
