/**
 * BuzzReach Mobile App entry point (MOBILE-001).
 *
 * Sets up:
 * - StatusBar configuration
 * - SafeAreaProvider for notch/inset handling
 * - AppNavigator with auth-gated routing
 *
 * Cross-module contracts:
 * - Integrates with MOBILE-002 (push notification foreground handler)
 */

import React from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";

import AppNavigator from "./src/navigation/AppNavigator";

/** Root app component. */
export default function App(): React.JSX.Element {
  return (
    <SafeAreaProvider>
      <StatusBar style="auto" />
      <AppNavigator />
    </SafeAreaProvider>
  );
}
