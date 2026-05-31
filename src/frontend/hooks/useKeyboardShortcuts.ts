/**
 * Hook for binding keyboard shortcuts (QUALITY-002).
 *
 * Attaches a global keydown listener that matches registered
 * shortcuts, suppresses when focus is in text inputs, and
 * cleans up on unmount.
 *
 * Cross-module contracts:
 * - Used by Dashboard (FE-002), Settings (FE-001), and all
 *   frontend pages that need keyboard interaction.
 */

import { useCallback, useEffect, useRef } from "react";

import type { ShortcutDef } from "../utils/keyboard";
import { isTextInput, matchesKey } from "../utils/keyboard";

/**
 * Register an array of keyboard shortcuts. Shortcuts are
 * suppressed when the user is typing in an input field.
 *
 * @param shortcuts - Array of shortcut definitions to bind.
 * @param enabled - Set false to temporarily disable all shortcuts.
 */
function useKeyboardShortcuts(
  shortcuts: ShortcutDef[],
  enabled: boolean = true
): void {
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent): void => {
      if (!enabled) return;
      if (isTextInput(event)) return;

      for (const shortcut of shortcutsRef.current) {
        if (matchesKey(event, shortcut.key)) {
          event.preventDefault();
          shortcut.handler();
          return;
        }
      }
    },
    [enabled]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown]);
}

export default useKeyboardShortcuts;
