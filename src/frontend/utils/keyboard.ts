/**
 * Keyboard shortcut helpers (QUALITY-002).
 *
 * Pure utility functions for key matching, input detection,
 * and shortcut definition types. No side effects.
 */

/** A single keyboard shortcut definition. */
export interface ShortcutDef {
  /** Human-readable key label (e.g. "j", "Shift+P", "Ctrl+K"). */
  key: string;
  /** Description shown in help modal. */
  description: string;
  /** Handler invoked when the shortcut fires. */
  handler: () => void;
  /** Optional group label for help modal sections. */
  group?: string;
}

/** Parsed representation of a key combo. */
interface KeyCombo {
  key: string;
  ctrl: boolean;
  shift: boolean;
  meta: boolean;
  alt: boolean;
}

/** Tags that indicate focus is in a text-editing context. */
const TEXT_INPUT_TAGS = new Set(["INPUT", "TEXTAREA", "SELECT"]);

/**
 * Returns true if the keyboard event target is a text field,
 * contentEditable, or similar. Shortcuts should be suppressed.
 */
export function isTextInput(event: KeyboardEvent): boolean {
  const target = event.target as HTMLElement | null;
  if (!target) return false;

  if (TEXT_INPUT_TAGS.has(target.tagName)) return true;
  if (target.isContentEditable) return true;
  if (target.getAttribute("role") === "textbox") return true;

  return false;
}

/**
 * Parse a key string like "Ctrl+K" or "Shift+P" into a KeyCombo.
 */
function parseKeyCombo(keyStr: string): KeyCombo {
  const parts = keyStr.split("+");
  const key = parts[parts.length - 1].toLowerCase();
  const modifiers = parts.slice(0, -1).map((m) => m.toLowerCase());

  return {
    key,
    ctrl: modifiers.includes("ctrl") || modifiers.includes("cmd"),
    shift: modifiers.includes("shift"),
    meta: modifiers.includes("meta") || modifiers.includes("cmd"),
    alt: modifiers.includes("alt"),
  };
}

/**
 * Check if a keyboard event matches a shortcut key string.
 *
 * Supports plain keys ("j"), modified keys ("Shift+P"),
 * and platform-aware modifiers ("Ctrl+K" matches Cmd+K on Mac).
 */
export function matchesKey(
  event: KeyboardEvent,
  keyStr: string
): boolean {
  const combo = parseKeyCombo(keyStr);
  const eventKey = event.key.toLowerCase();

  if (eventKey !== combo.key) return false;

  if (keyStr === "?") {
    return event.shiftKey && eventKey === "?";
  }

  const needsCtrl = combo.ctrl || combo.meta;
  const hasCtrl = event.ctrlKey || event.metaKey;

  if (needsCtrl !== hasCtrl) return false;
  if (combo.shift !== event.shiftKey) return false;
  if (combo.alt !== event.altKey) return false;

  return true;
}

/**
 * Format a key string for display in the help modal.
 * Replaces "Ctrl" with platform-appropriate modifier.
 */
export function formatKeyForDisplay(keyStr: string): string {
  const isMac =
    typeof navigator !== "undefined" &&
    navigator.platform.includes("Mac");

  if (isMac) {
    return keyStr.replace("Ctrl", "\u2318").replace("Shift", "\u21E7");
  }

  return keyStr;
}

/**
 * Group shortcuts by their group label for display in help modal.
 */
export function groupShortcuts(
  shortcuts: ShortcutDef[]
): Map<string, ShortcutDef[]> {
  const groups = new Map<string, ShortcutDef[]>();

  for (const shortcut of shortcuts) {
    const group = shortcut.group ?? "General";
    const existing = groups.get(group);
    if (existing) {
      existing.push(shortcut);
    } else {
      groups.set(group, [shortcut]);
    }
  }

  return groups;
}
