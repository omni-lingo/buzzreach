/**
 * Settings screen stub for BuzzReach mobile app (MOBILE-001).
 *
 * Displays:
 * - Current user info (username, email)
 * - API base URL configuration
 * - Notification toggle
 * - Logout button
 *
 * Full settings impl deferred to later atoms.
 *
 * Cross-module contracts:
 * - Uses UserData from auth store
 * - Integrates with MOBILE-002 (push notifications)
 */

import React from "react";
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from "react-native";

import { logout } from "../hooks/useAuth";
import useColorTheme from "../hooks/useColorTheme";
import { useAuthStore } from "../store/authStore";
import { useSettingsStore } from "../store/settingsStore";

/** Settings screen with user info and app configuration. */
function SettingsScreen(): React.JSX.Element {
  const user = useAuthStore((s) => s.user);
  const apiBaseUrl = useSettingsStore((s) => s.apiBaseUrl);
  const notificationsEnabled = useSettingsStore(
    (s) => s.notificationsEnabled
  );
  const { colors } = useColorTheme();

  function handleLogout(): void {
    Alert.alert("Sign Out", "Are you sure you want to sign out?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Sign Out",
        style: "destructive",
        onPress: () => void logout(),
      },
    ]);
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={styles.content}
    >
      <SectionHeader title="Account" color={colors.textTertiary} />
      <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <InfoRow label="Username" value={user?.username ?? "—"} colors={colors} />
        <InfoRow label="Email" value={user?.email ?? "—"} colors={colors} />
      </View>

      <SectionHeader title="Configuration" color={colors.textTertiary} />
      <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>
          API Server URL
        </Text>
        <TextInput
          style={[styles.input, { backgroundColor: colors.inputBg, borderColor: colors.borderStrong, color: colors.text }]}
          value={apiBaseUrl}
          onChangeText={useSettingsStore.getState().setApiBaseUrl}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
          placeholder="https://api.buzzreach.app"
          placeholderTextColor={colors.textTertiary}
        />
      </View>

      <SectionHeader title="Notifications" color={colors.textTertiary} />
      <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <View style={styles.switchRow}>
          <Text style={[styles.switchLabel, { color: colors.text }]}>
            Push Notifications
          </Text>
          <Switch
            value={notificationsEnabled}
            onValueChange={
              useSettingsStore.getState().setNotificationsEnabled
            }
            trackColor={{ false: colors.switchTrack, true: colors.primary }}
          />
        </View>
      </View>

      <Pressable style={[styles.logoutButton, { backgroundColor: colors.error }]} onPress={handleLogout}>
        <Text style={styles.logoutText}>Sign Out</Text>
      </Pressable>

      <Text style={[styles.version, { color: colors.textTertiary }]}>
        BuzzReach Mobile v1.0.0
      </Text>
    </ScrollView>
  );
}

// --------------- Sub-components ---------------

function SectionHeader(props: {
  title: string;
  color: string;
}): React.JSX.Element {
  return (
    <Text style={[styles.sectionHeader, { color: props.color }]}>
      {props.title}
    </Text>
  );
}

function InfoRow(props: {
  label: string;
  value: string;
  colors: { textSecondary: string; text: string };
}): React.JSX.Element {
  return (
    <View style={styles.infoRow}>
      <Text style={[styles.infoLabel, { color: props.colors.textSecondary }]}>
        {props.label}
      </Text>
      <Text style={[styles.infoValue, { color: props.colors.text }]}>
        {props.value}
      </Text>
    </View>
  );
}

// --------------- Styles ---------------

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 40 },
  sectionHeader: {
    fontSize: 13,
    fontWeight: "600",
    textTransform: "uppercase",
    marginTop: 24,
    marginBottom: 8,
    marginLeft: 4,
  },
  card: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
  },
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
  },
  infoLabel: { fontSize: 15 },
  infoValue: { fontSize: 15, fontWeight: "500" },
  fieldLabel: { fontSize: 13, marginBottom: 6 },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
  },
  switchRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 4,
  },
  switchLabel: { fontSize: 15 },
  logoutButton: {
    marginTop: 32,
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: "center",
  },
  logoutText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  version: {
    textAlign: "center",
    fontSize: 12,
    marginTop: 24,
  },
});

export default SettingsScreen;
