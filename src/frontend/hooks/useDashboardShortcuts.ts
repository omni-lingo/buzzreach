/**
 * Dashboard-specific keyboard shortcuts (QUALITY-002).
 *
 * Wires j/k navigation, c/o/a/p/r actions, ? help modal,
 * Escape close to the Dashboard page.
 */

import { useCallback, useMemo, useState } from "react";

import type { Opportunity } from "../api/opportunitiesClient";
import type { ShortcutDef } from "../utils/keyboard";
import useKeyboardShortcuts from "./useKeyboardShortcuts";

interface DashboardShortcutsConfig {
  opportunities: Opportunity[];
  onMarkPosted: (id: string) => void;
  onArchive: (id: string) => void;
  onRefresh: () => void;
}

interface DashboardShortcutsReturn {
  activeIndex: number;
  helpVisible: boolean;
  shortcuts: ShortcutDef[];
  closeHelp: () => void;
}

interface NavigationActions {
  moveNext: () => void;
  movePrev: () => void;
  getActiveOpp: () => Opportunity | null;
}

function useNavigation(
  opportunities: Opportunity[]
): [number, NavigationActions] {
  const [activeIndex, setActiveIndex] = useState(-1);

  const getActiveOpp = useCallback((): Opportunity | null => {
    if (activeIndex < 0 || activeIndex >= opportunities.length) {
      return null;
    }
    return opportunities[activeIndex];
  }, [activeIndex, opportunities]);

  const moveNext = useCallback((): void => {
    setActiveIndex((prev) => {
      if (opportunities.length === 0) return -1;
      if (prev < 0) return 0;
      return (prev + 1) % opportunities.length;
    });
  }, [opportunities.length]);

  const movePrev = useCallback((): void => {
    setActiveIndex((prev) => {
      if (opportunities.length === 0) return -1;
      if (prev <= 0) return opportunities.length - 1;
      return prev - 1;
    });
  }, [opportunities.length]);

  return [activeIndex, { moveNext, movePrev, getActiveOpp }];
}

interface CardActions {
  copyDraft: () => void;
  openThread: () => void;
  archiveFocused: () => void;
  markPostedFocused: () => void;
}

function useCardActions(
  getActiveOpp: () => Opportunity | null,
  onArchive: (id: string) => void,
  onMarkPosted: (id: string) => void
): CardActions {
  const copyDraft = useCallback((): void => {
    const opp = getActiveOpp();
    if (!opp) return;
    navigator.clipboard.writeText(opp.draft_reply).catch(() => {});
  }, [getActiveOpp]);

  const openThread = useCallback((): void => {
    const opp = getActiveOpp();
    if (!opp) return;
    window.open(opp.url, "_blank", "noopener,noreferrer");
  }, [getActiveOpp]);

  const archiveFocused = useCallback((): void => {
    const opp = getActiveOpp();
    if (!opp) return;
    onArchive(opp.id);
  }, [getActiveOpp, onArchive]);

  const markPostedFocused = useCallback((): void => {
    const opp = getActiveOpp();
    if (!opp) return;
    onMarkPosted(opp.id);
  }, [getActiveOpp, onMarkPosted]);

  return { copyDraft, openThread, archiveFocused, markPostedFocused };
}

function buildShortcuts(
  nav: NavigationActions,
  card: CardActions,
  onRefresh: () => void,
  showHelp: () => void,
  closeHelp: () => void
): ShortcutDef[] {
  return [
    { key: "j", description: "Next opportunity", handler: nav.moveNext, group: "Navigation" },
    { key: "k", description: "Previous opportunity", handler: nav.movePrev, group: "Navigation" },
    { key: "c", description: "Copy draft to clipboard", handler: card.copyDraft, group: "Actions" },
    { key: "o", description: "Open thread in new tab", handler: card.openThread, group: "Actions" },
    { key: "a", description: "Archive opportunity", handler: card.archiveFocused, group: "Actions" },
    { key: "p", description: "Mark as posted", handler: card.markPostedFocused, group: "Actions" },
    { key: "r", description: "Regenerate / refresh", handler: onRefresh, group: "Actions" },
    { key: "?", description: "Show keyboard shortcuts", handler: showHelp, group: "General" },
    { key: "Escape", description: "Close modal", handler: closeHelp, group: "General" },
  ];
}

function useDashboardShortcuts(
  config: DashboardShortcutsConfig
): DashboardShortcutsReturn {
  const { opportunities, onMarkPosted, onArchive, onRefresh } = config;

  const [helpVisible, setHelpVisible] = useState(false);
  const [activeIndex, nav] = useNavigation(opportunities);
  const card = useCardActions(nav.getActiveOpp, onArchive, onMarkPosted);

  const showHelp = useCallback((): void => setHelpVisible(true), []);
  const closeHelp = useCallback((): void => setHelpVisible(false), []);

  const shortcuts = useMemo(
    () => buildShortcuts(nav, card, onRefresh, showHelp, closeHelp),
    [nav, card, onRefresh, showHelp, closeHelp]
  );

  useKeyboardShortcuts(shortcuts, !helpVisible);

  return { activeIndex, helpVisible, shortcuts, closeHelp };
}

export default useDashboardShortcuts;
