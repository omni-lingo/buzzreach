/**
 * Optional shortcut bar for mobile accessibility (QUALITY-002).
 *
 * Shows a horizontal row of labelled action buttons at the bottom
 * of the feed screen. Each button triggers the same action as
 * the keyboard shortcut on desktop.
 *
 * Cross-module contracts:
 * - Used by FeedScreen (MOBILE-003) as an optional overlay.
 * - Actions mirror Dashboard keyboard shortcuts.
 */

import React from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

interface ShortcutAction {
  label: string;
  shortcutKey: string;
  onPress: () => void;
  disabled?: boolean;
}

interface ShortcutBarProps {
  actions: ShortcutAction[];
  visible: boolean;
}

/** Horizontal scrollable bar of shortcut buttons. */
function ShortcutBar({
  actions,
  visible,
}: ShortcutBarProps): React.JSX.Element | null {
  if (!visible) return null;

  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {actions.map((action) => (
          <ShortcutButton
            key={action.shortcutKey}
            action={action}
          />
        ))}
      </ScrollView>
    </View>
  );
}

function ShortcutButton({
  action,
}: {
  action: ShortcutAction;
}): React.JSX.Element {
  return (
    <TouchableOpacity
      style={[
        styles.button,
        action.disabled ? styles.buttonDisabled : null,
      ]}
      onPress={action.onPress}
      disabled={action.disabled}
      accessibilityRole="button"
      accessibilityLabel={action.label}
    >
      <Text style={styles.keyLabel}>{action.shortcutKey}</Text>
      <Text style={styles.actionLabel}>{action.label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#ffffff",
    borderTopWidth: 1,
    borderTopColor: "#e0e0e0",
    paddingVertical: 8,
  },
  scrollContent: {
    paddingHorizontal: 12,
    gap: 8,
  },
  button: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#f5f5f5",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    minHeight: 44,
    gap: 6,
  },
  buttonDisabled: {
    opacity: 0.4,
  },
  keyLabel: {
    fontSize: 12,
    fontWeight: "700",
    color: "#FF6B35",
    backgroundColor: "#fff3ed",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    overflow: "hidden",
  },
  actionLabel: {
    fontSize: 13,
    color: "#333333",
    fontWeight: "500",
  },
});

export default ShortcutBar;
export type { ShortcutAction };
