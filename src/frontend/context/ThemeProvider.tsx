/**
 * Theme context provider (QUALITY-001).
 *
 * Wraps the app to provide theme state to all child components.
 * Uses useTheme hook internally and exposes theme + toggle via context.
 *
 * Cross-module contracts:
 * - Consumed by all frontend components that need theme awareness
 * - ThemeToggle component reads from this context
 */

import React, { createContext, useContext } from "react";

import useTheme from "../hooks/useTheme";
import type { Theme, ThemeState } from "../hooks/useTheme";

const ThemeContext = createContext<ThemeState>({
  theme: "light",
  toggleTheme: () => {},
});

interface ThemeProviderProps {
  children: React.ReactNode;
}

/** Provides theme context to all children. */
function ThemeProvider({ children }: ThemeProviderProps): React.JSX.Element {
  const themeState = useTheme();

  return (
    <ThemeContext.Provider value={themeState}>
      {children}
    </ThemeContext.Provider>
  );
}

/** Access theme state from any component inside ThemeProvider. */
function useThemeContext(): ThemeState {
  return useContext(ThemeContext);
}

export { ThemeContext, ThemeProvider, useThemeContext };
export type { Theme };
