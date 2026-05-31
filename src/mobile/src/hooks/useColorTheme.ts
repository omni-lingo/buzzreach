/**
 * Mobile color theme hook (QUALITY-001).
 *
 * Detects system dark/light mode preference via React Native's
 * useColorScheme and provides both navigation theme and component colors.
 *
 * Cross-module contracts:
 * - Used by AppNavigator for navigation theme
 * - Used by all mobile screens/components for dynamic styling
 */

import { useColorScheme } from "react-native";
import type { Theme } from "@react-navigation/native";

type ColorMode = "light" | "dark";

interface AppColors {
  primary: string;
  background: string;
  card: string;
  text: string;
  textSecondary: string;
  textTertiary: string;
  border: string;
  borderStrong: string;
  inputBg: string;
  error: string;
  success: string;
  switchTrack: string;
}

const LIGHT_COLORS: AppColors = {
  primary: "#FF6B35",
  background: "#f8f9fa",
  card: "#ffffff",
  text: "#333333",
  textSecondary: "#666666",
  textTertiary: "#999999",
  border: "#e9ecef",
  borderStrong: "#dddddd",
  inputBg: "#f8f9fa",
  error: "#dc3545",
  success: "#28a745",
  switchTrack: "#dddddd",
};

const DARK_COLORS: AppColors = {
  primary: "#FF7B45",
  background: "#1a1a2e",
  card: "#16213e",
  text: "#e0e0e0",
  textSecondary: "#b0b0b0",
  textTertiary: "#808080",
  border: "#2a2a4a",
  borderStrong: "#3a3a5a",
  inputBg: "#1a1a2e",
  error: "#e74c5c",
  success: "#34d399",
  switchTrack: "#3a3a5a",
};

/** Build navigation theme from color mode. */
function buildNavTheme(mode: ColorMode): Theme {
  const colors = mode === "dark" ? DARK_COLORS : LIGHT_COLORS;
  return {
    dark: mode === "dark",
    colors: {
      primary: colors.primary,
      background: colors.background,
      card: colors.card,
      text: colors.text,
      border: colors.border,
      notification: colors.primary,
    },
    fonts: {
      regular: { fontFamily: "System", fontWeight: "400" },
      medium: { fontFamily: "System", fontWeight: "500" },
      bold: { fontFamily: "System", fontWeight: "700" },
      heavy: { fontFamily: "System", fontWeight: "900" },
    },
  };
}

interface ColorThemeState {
  colorMode: ColorMode;
  colors: AppColors;
  navTheme: Theme;
  isDark: boolean;
}

/** Hook returning system-aware color theme for mobile components. */
function useColorTheme(): ColorThemeState {
  const systemScheme = useColorScheme();
  const colorMode: ColorMode = systemScheme === "dark" ? "dark" : "light";
  const colors = colorMode === "dark" ? DARK_COLORS : LIGHT_COLORS;
  const navTheme = buildNavTheme(colorMode);

  return { colorMode, colors, navTheme, isDark: colorMode === "dark" };
}

export { DARK_COLORS, LIGHT_COLORS, buildNavTheme };
export type { AppColors, ColorMode, ColorThemeState };
export default useColorTheme;
