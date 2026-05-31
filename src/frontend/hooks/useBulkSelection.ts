/**
 * Bulk selection state management hook (FEAT-006).
 *
 * Manages a Set of selected opportunity IDs with toggle, select-all,
 * deselect-all, and count utilities.
 */

import { useCallback, useState } from "react";

interface UseBulkSelectionReturn {
  selected: Set<string>;
  count: number;
  isSelected: (id: string) => boolean;
  toggle: (id: string) => void;
  selectAll: (ids: string[]) => void;
  deselectAll: () => void;
}

function useBulkSelection(): UseBulkSelectionReturn {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggle = useCallback((id: string): void => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const selectAll = useCallback((ids: string[]): void => {
    setSelected(new Set(ids));
  }, []);

  const deselectAll = useCallback((): void => {
    setSelected(new Set());
  }, []);

  const isSelected = useCallback(
    (id: string): boolean => selected.has(id),
    [selected]
  );

  return {
    selected,
    count: selected.size,
    isSelected,
    toggle,
    selectAll,
    deselectAll,
  };
}

export default useBulkSelection;
export type { UseBulkSelectionReturn };
