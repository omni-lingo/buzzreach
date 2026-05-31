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
import { useAuthStore } from "../store/authStore";
import { useSettingsStore } from "../store/settingsStore";

/** Settings screen with user info and app configuration. */
function SettingsScreen(): React.JSX.Element {
  const user = useAuthStore((s) => s.user);
  const apiBaseUrl = useSettingsStore((s) => s.apiBaseUrl);
  const notificationsEnabled = useSettingsStore(
    (s) => s.notificationsEnabled
  );

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
      style={styles.container}
      contentContainerStyle={styles.content}
    >
      <SectionHeader title="Account" />
      <View style={styles.card}>
        <InfoRow label="Username" value={user?.username ?? "—"} />
        <InfoRow label="Email" value={user?.email ?? "—"} />
      </View>

      <SectionHeader title="Configuration" />
      <View style={styles.card}>
        <Text style={styles.fieldLabel}>API Server URL</Text>
        <TextInput
          style={styles.input}
          value={apiBaseUrl}
          onChangeText={useSettingsStore.getState().setApiBaseUrl}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
          placeholder="https://api.buzzreach.app"
          placeholderTextColor="#999"
        />
      </View>

      <SectionHeader title="Notifications" />
      <View style={styles.card}>
        <View style={styles.switchRow}>
          <Text style={styles.switchLabel}>Push Notifications</Text>
          <Switch
            value={notificationsEnabled}
            onValueChange={
              useSettingsStore.getState().setNotificationsEnabled
            }
            trackColor={{ false: "#ddd", true: "#FF6B35" }}
          />
        </View>
      </View>

      <Pressable style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Sign Out</Text>
      </Pressable>

      <Text style={styles.version}>BuzzReach Mobile v1.0.0</Text>
    </ScrollView>
  );
}

// --------------- Sub-components ---------------

function SectionHeader(props: { title: string }): React.JSX.Element {
  return <Text style={styles.sectionHeader}>{props.title}</Text>;
}

function InfoRow(props: {
  label: string;
  value: string;
}): React.JSX.Element {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{props.label}</Text>
      <Text style={styles.infoValue}>{props.value}</Text>
    </View>
  );
}

// --------------- Styles ---------------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  content: { padding: 16, paddingBottom: 40 },
  sectionHeader: {
    fontSize: 13,
    fontWeight: "600",
    color: "#999",
    textTransform: "uppercase",
    marginTop: 24,
    marginBottom: 8,
    marginLeft: 4,
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: "#e9ecef",
  },
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
  },
  infoLabel: { fontSize: 15, color: "#666" },
  infoValue: { fontSize: 15, color: "#333", fontWeight: "500" },
  fieldLabel: { fontSize: 13, color: "#666", marginBottom: 6 },
  input: {
    backgroundColor: "#f8f9fa",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: "#333",
  },
  switchRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 4,
  },
  switchLabel: { fontSize: 15, color: "#333" },
  logoutButton: {
    marginTop: 32,
    backgroundColor: "#dc3545",
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: "center",
  },
  logoutText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  version: {
    textAlign: "center",
    color: "#ccc",
    fontSize: 12,
    marginTop: 24,
  },
});

export default SettingsScreen;
