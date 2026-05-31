/**
 * Keyboard Help modal (QUALITY-002).
 *
 * Displays available shortcuts grouped by context.
 * Keyboard-navigable: arrow keys move selection, Escape closes.
 *
 * Cross-module contracts:
 * - Receives ShortcutDef[] from parent page components.
 * - Used by Dashboard (FE-002), Settings (FE-001), etc.
 */

import React, { useCallback, useEffect, useRef, useState } from "react";

import type { ShortcutDef } from "../utils/keyboard";
import {
  formatKeyForDisplay,
  groupShortcuts,
} from "../utils/keyboard";

interface KeyboardHelpProps {
  shortcuts: ShortcutDef[];
  visible: boolean;
  onClose: () => void;
}

function useModalNavigation(
  visible: boolean,
  itemCount: number,
  onClose: () => void
): number {
  const [activeIndex, setActiveIndex] = useState(0);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent): void => {
      if (!visible) return;
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActiveIndex((p) => (p < itemCount - 1 ? p + 1 : 0));
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setActiveIndex((p) => (p > 0 ? p - 1 : itemCount - 1));
      }
    },
    [visible, onClose, itemCount]
  );

  useEffect(() => {
    if (!visible) return;
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [visible, handleKeyDown]);

  useEffect(() => {
    if (visible) setActiveIndex(0);
  }, [visible]);

  return activeIndex;
}

const KeyboardHelp: React.FC<KeyboardHelpProps> = ({
  shortcuts,
  visible,
  onClose,
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);
  const groups = groupShortcuts(shortcuts);
  const flatList = shortcuts.filter((s) => s.key !== "?");
  const activeIndex = useModalNavigation(visible, flatList.length, onClose);

  const handleOverlayClick = useCallback(
    (event: React.MouseEvent): void => {
      if (event.target === overlayRef.current) onClose();
    },
    [onClose]
  );

  if (!visible) return null;

  return (
    <div
      className="keyboard-help-overlay"
      ref={overlayRef}
      onClick={handleOverlayClick}
      role="dialog"
      aria-label="Keyboard shortcuts"
      aria-modal="true"
    >
      <div className="keyboard-help-modal">
        <ModalHeader onClose={onClose} />
        <ModalBody
          groups={groups}
          flatList={flatList}
          activeIndex={activeIndex}
        />
      </div>
    </div>
  );
};

// --------------- Sub-components ---------------

const ModalHeader: React.FC<{ onClose: () => void }> = ({
  onClose,
}) => (
  <div className="keyboard-help-header">
    <h2>Keyboard Shortcuts</h2>
    <button
      className="keyboard-help-close"
      onClick={onClose}
      type="button"
      aria-label="Close keyboard shortcuts"
    >
      &times;
    </button>
  </div>
);

interface ModalBodyProps {
  groups: Map<string, ShortcutDef[]>;
  flatList: ShortcutDef[];
  activeIndex: number;
}

const ModalBody: React.FC<ModalBodyProps> = ({
  groups,
  flatList,
  activeIndex,
}) => (
  <div className="keyboard-help-body">
    {Array.from(groups.entries()).map(([groupName, items]) => (
      <ShortcutGroup
        key={groupName}
        name={groupName}
        items={items}
        activeIndex={activeIndex}
        allShortcuts={flatList}
      />
    ))}
  </div>
);

interface ShortcutGroupProps {
  name: string;
  items: ShortcutDef[];
  activeIndex: number;
  allShortcuts: ShortcutDef[];
}

const ShortcutGroup: React.FC<ShortcutGroupProps> = ({
  name,
  items,
  activeIndex,
  allShortcuts,
}) => (
  <div className="shortcut-group">
    <h3 className="shortcut-group-title">{name}</h3>
    {items
      .filter((s) => s.key !== "?")
      .map((shortcut) => {
        const isActive =
          allShortcuts.indexOf(shortcut) === activeIndex;
        return (
          <ShortcutRow
            key={shortcut.key}
            shortcut={shortcut}
            isActive={isActive}
          />
        );
      })}
  </div>
);

const ShortcutRow: React.FC<{ shortcut: ShortcutDef; isActive: boolean }> = ({
  shortcut,
  isActive,
}) => (
  <div
    className={`shortcut-row${isActive ? " shortcut-active" : ""}`}
  >
    <kbd className="shortcut-key">
      {formatKeyForDisplay(shortcut.key)}
    </kbd>
    <span className="shortcut-desc">{shortcut.description}</span>
  </div>
);

export default KeyboardHelp;
