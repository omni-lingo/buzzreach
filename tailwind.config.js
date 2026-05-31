/**
 * Tailwind CSS configuration with dark mode support (QUALITY-001).
 *
 * Uses "class" strategy so dark mode is toggled via [data-theme="dark"]
 * attribute on <html>, matching the CSS custom properties approach.
 *
 * Cross-module contracts:
 * - Works alongside src/frontend/styles/dark.css for theme variables
 * - All frontend components can use dark: prefix utilities
 */

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/frontend/**/*.{ts,tsx}", "./src/desktop/**/*.{ts,tsx}"],

  darkMode: ["selector", '[data-theme="dark"]'],

  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "var(--accent-primary)",
          hover: "var(--accent-primary-hover)",
        },
        surface: {
          primary: "var(--bg-primary)",
          secondary: "var(--bg-secondary)",
          tertiary: "var(--bg-tertiary)",
        },
        content: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          tertiary: "var(--text-tertiary)",
          inverse: "var(--text-inverse)",
        },
        border: {
          DEFAULT: "var(--border-color)",
          strong: "var(--border-color-strong)",
        },
      },
      backgroundColor: {
        card: "var(--card-bg)",
        input: "var(--input-bg)",
      },
      borderColor: {
        card: "var(--card-border)",
        input: "var(--input-border)",
      },
      textColor: {
        input: "var(--input-text)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
      },
    },
  },

  plugins: [],
};
