/**
 * Clipboard utility for copy-to-clipboard actions (MOBILE-004).
 *
 * Provides:
 * - copyDraft: copies draft text to system clipboard
 * - clearClipboard: clears clipboard (privacy, logout)
 * - buildClipboardText: assembles text with optional footer
 *
 * Uses expo-clipboard which works in background (clipboard accessible
 * after app is backgrounded). No network calls needed — pure local.
 *
 * Cross-module contracts:
 * - Consumed by OpportunityActions component (MOBILE-004)
 * - clearClipboard called on logout via useAuth hook
 */

import * as Clipboard from "expo-clipboard";

const FOOTER_TEXT = "Posted via BuzzReach";

/**
 * Build clipboard text from draft with optional footer.
 * Footer is appended with double newline separator.
 */
function buildClipboardText(
  draft: string,
  includeFooter: boolean
): string {
  if (!includeFooter) {
    return draft;
  }
  return `${draft}\n\n${FOOTER_TEXT}`;
}

/**
 * Copy draft text to system clipboard.
 * Returns true on success, false on failure.
 */
async function copyDraft(
  draft: string,
  includeFooter: boolean
): Promise<boolean> {
  const text = buildClipboardText(draft, includeFooter);
  try {
    await Clipboard.setStringAsync(text);
    return true;
  } catch {
    return false;
  }
}

/**
 * Clear clipboard contents (privacy).
 * Called on logout and manual clear from settings.
 */
async function clearClipboard(): Promise<void> {
  await Clipboard.setStringAsync("");
}

export { buildClipboardText, clearClipboard, copyDraft };
