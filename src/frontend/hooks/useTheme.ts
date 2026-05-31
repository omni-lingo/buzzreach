/**
 * Theme hook for dark mode support (QUALITY-001).
 *
 * Returns { theme, toggleTheme } for components to read and switch theme.
 * - Persists user preference in localStorage
 * - Detects system preference via prefers-color-scheme media query
 * - Sets data-theme attribute on <html> for CSS variable switching
 *
 * Cross-module contracts:
 * - Used by ThemeProvider to supply context to all components
 * - Used by all frontend modules (FE-001, FE-002, MOBILE-003, etc.)
 */

import { useCallback, useEffect, useMemo, useState } from "react";

type Theme = "light" | "dark";

interface ThemeState {
  theme: Theme;
  toggleTheme: () => void;
}

const STORAGE_KEY = "buzzreach-theme";

/** Read system color-scheme preference. */
function getSystemPreference(): Theme {
  if (
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    return "dark";
  }
  return "light";
}

/** Read stored preference, falling back to system preference. */
function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";

  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return getSystemPreference();
}

/** Apply theme to the DOM without React re-render. */
function applyTheme(theme: Theme): void {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", theme);
}

/**
 * Hook providing theme state and toggle.
 *
 * Must be used inside ThemeProvider or at app root.
 */
function useTheme(): ThemeState {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = (e: MediaQueryListEvent): void => {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) {
        setTheme(e.matches ? "dark" : "light");
      }
    };

    mq.addEventListener("change", handleChange);
    return () => mq.removeEventListener("change", handleChange);
  }, []);

  const toggleTheme = useCallback((): void => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  }, []);

  return useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme]);
}

export { getInitialTheme, getSystemPreference, STORAGE_KEY };
export type { Theme, ThemeState };
export default useTheme;
