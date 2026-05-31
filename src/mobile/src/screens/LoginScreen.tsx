/**
 * Login screen for BuzzReach mobile app (MOBILE-001).
 *
 * Supports two auth methods:
 * 1. Username + password login
 * 2. API key login (from settings page)
 *
 * Auth token is persisted to SecureStore on success.
 * Navigation to Feed screen happens automatically via auth state.
 *
 * Cross-module contracts:
 * - Calls POST /api/v1/auth/login (username/password)
 * - Calls POST /api/v1/auth/login-api-key (API key)
 */

import React, { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { loginWithApiKey, loginWithCredentials } from "../hooks/useAuth";
import { useAuthStore } from "../store/authStore";

type LoginMode = "credentials" | "apikey";

/** Login screen with tabbed credential/API key inputs. */
function LoginScreen(): React.JSX.Element {
  const [mode, setMode] = useState<LoginMode>("credentials");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [apiKey, setApiKey] = useState("");

  const isLoading = useAuthStore((s) => s.isLoading);
  const error = useAuthStore((s) => s.error);

  async function handleLogin(): Promise<void> {
    if (mode === "credentials") {
      if (!username.trim() || !password.trim()) {
        return;
      }
      await loginWithCredentials(username.trim(), password);
    } else {
      if (!apiKey.trim()) {
        return;
      }
      await loginWithApiKey(apiKey.trim());
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View style={styles.header}>
        <Text style={styles.title}>BuzzReach</Text>
        <Text style={styles.subtitle}>
          Sign in to access your opportunities
        </Text>
      </View>

      <View style={styles.tabs}>
        <Pressable
          style={[styles.tab, mode === "credentials" && styles.activeTab]}
          onPress={() => setMode("credentials")}
        >
          <Text style={styles.tabText}>Password</Text>
        </Pressable>
        <Pressable
          style={[styles.tab, mode === "apikey" && styles.activeTab]}
          onPress={() => setMode("apikey")}
        >
          <Text style={styles.tabText}>API Key</Text>
        </Pressable>
      </View>

      {mode === "credentials" ? (
        <CredentialsForm
          username={username}
          password={password}
          onUsernameChange={setUsername}
          onPasswordChange={setPassword}
        />
      ) : (
        <ApiKeyForm apiKey={apiKey} onApiKeyChange={setApiKey} />
      )}

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Pressable
        style={[styles.button, isLoading && styles.buttonDisabled]}
        onPress={handleLogin}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Sign In</Text>
        )}
      </Pressable>
    </KeyboardAvoidingView>
  );
}

// --------------- Sub-components ---------------

interface CredentialsFormProps {
  username: string;
  password: string;
  onUsernameChange: (v: string) => void;
  onPasswordChange: (v: string) => void;
}

function CredentialsForm(props: CredentialsFormProps): React.JSX.Element {
  return (
    <View style={styles.form}>
      <TextInput
        style={styles.input}
        placeholder="Username"
        placeholderTextColor="#999"
        value={props.username}
        onChangeText={props.onUsernameChange}
        autoCapitalize="none"
        autoCorrect={false}
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        placeholderTextColor="#999"
        value={props.password}
        onChangeText={props.onPasswordChange}
        secureTextEntry
      />
    </View>
  );
}

interface ApiKeyFormProps {
  apiKey: string;
  onApiKeyChange: (v: string) => void;
}

function ApiKeyForm(props: ApiKeyFormProps): React.JSX.Element {
  return (
    <View style={styles.form}>
      <TextInput
        style={styles.input}
        placeholder="API Key (bz_...)"
        placeholderTextColor="#999"
        value={props.apiKey}
        onChangeText={props.onApiKeyChange}
        autoCapitalize="none"
        autoCorrect={false}
      />
      <Text style={styles.hint}>
        Find your API key in the web dashboard under Settings.
      </Text>
    </View>
  );
}

// --------------- Styles ---------------

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    padding: 24,
    backgroundColor: "#f8f9fa",
  },
  header: { alignItems: "center", marginBottom: 32 },
  title: { fontSize: 32, fontWeight: "bold", color: "#FF6B35" },
  subtitle: { fontSize: 14, color: "#666", marginTop: 8 },
  tabs: { flexDirection: "row", marginBottom: 16 },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: "center",
    borderBottomWidth: 2,
    borderBottomColor: "#ddd",
  },
  activeTab: { borderBottomColor: "#FF6B35" },
  tabText: { fontSize: 14, fontWeight: "600", color: "#333" },
  form: { marginBottom: 16 },
  input: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 14,
    fontSize: 16,
    marginBottom: 12,
    color: "#333",
  },
  hint: { fontSize: 12, color: "#999", marginTop: 4 },
  error: {
    color: "#dc3545",
    fontSize: 14,
    textAlign: "center",
    marginBottom: 12,
  },
  button: {
    backgroundColor: "#FF6B35",
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: "center",
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
});

export default LoginScreen;
