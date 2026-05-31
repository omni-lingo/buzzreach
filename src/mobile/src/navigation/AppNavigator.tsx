/**
 * App navigation with auth-gated routing (MOBILE-001).
 *
 * Routing logic:
 * - While auth state loads: splash / loading screen
 * - Not authenticated: LoginScreen
 * - Authenticated: Bottom tab navigator (Feed, Settings)
 *
 * Cross-module contracts:
 * - Uses auth store to determine route
 * - Integrates with MOBILE-002 (push notification deep links)
 */

import {
  NavigationContainer,
  type Theme,
} from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import React, { useEffect } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { restoreAuth } from "../hooks/useAuth";
import FeedScreen from "../screens/FeedScreen";
import LoginScreen from "../screens/LoginScreen";
import SettingsScreen from "../screens/SettingsScreen";
import { useAuthStore } from "../store/authStore";

type AuthStackParams = {
  Login: undefined;
};

type MainTabParams = {
  Feed: undefined;
  Settings: undefined;
};

type RootStackParams = {
  Auth: undefined;
  Main: undefined;
};

const RootStack = createNativeStackNavigator<RootStackParams>();
const AuthStack = createNativeStackNavigator<AuthStackParams>();
const MainTab = createBottomTabNavigator<MainTabParams>();

const NAV_THEME: Theme = {
  dark: false,
  colors: {
    primary: "#FF6B35",
    background: "#f8f9fa",
    card: "#ffffff",
    text: "#333333",
    border: "#e9ecef",
    notification: "#FF6B35",
  },
  fonts: {
    regular: { fontFamily: "System", fontWeight: "400" },
    medium: { fontFamily: "System", fontWeight: "500" },
    bold: { fontFamily: "System", fontWeight: "700" },
    heavy: { fontFamily: "System", fontWeight: "900" },
  },
};

/** Auth-gated root navigator. */
function AppNavigator(): React.JSX.Element {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isInitialized = useAuthStore((s) => s.isInitialized);

  useEffect(() => {
    void restoreAuth();
  }, []);

  if (!isInitialized) {
    return <SplashLoading />;
  }

  return (
    <NavigationContainer theme={NAV_THEME}>
      <RootStack.Navigator screenOptions={{ headerShown: false }}>
        {isAuthenticated ? (
          <RootStack.Screen name="Main" component={MainTabs} />
        ) : (
          <RootStack.Screen name="Auth" component={AuthScreens} />
        )}
      </RootStack.Navigator>
    </NavigationContainer>
  );
}

/** Auth stack: login screen only. */
function AuthScreens(): React.JSX.Element {
  return (
    <AuthStack.Navigator screenOptions={{ headerShown: false }}>
      <AuthStack.Screen name="Login" component={LoginScreen} />
    </AuthStack.Navigator>
  );
}

/** Main tab navigator for authenticated users. */
function MainTabs(): React.JSX.Element {
  return (
    <MainTab.Navigator
      screenOptions={{
        tabBarActiveTintColor: "#FF6B35",
        tabBarInactiveTintColor: "#999",
        headerStyle: { backgroundColor: "#FF6B35" },
        headerTintColor: "#fff",
        headerTitleStyle: { fontWeight: "600" },
      }}
    >
      <MainTab.Screen
        name="Feed"
        component={FeedScreen}
        options={{
          title: "Opportunities",
          tabBarLabel: "Feed",
          tabBarIcon: ({ color }) => (
            <Text style={{ color, fontSize: 20 }}>&#9733;</Text>
          ),
        }}
      />
      <MainTab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: "Settings",
          tabBarIcon: ({ color }) => (
            <Text style={{ color, fontSize: 20 }}>&#9881;</Text>
          ),
        }}
      />
    </MainTab.Navigator>
  );
}

/** Splash screen shown while restoring auth state. */
function SplashLoading(): React.JSX.Element {
  return (
    <View style={styles.splash}>
      <Text style={styles.splashTitle}>BuzzReach</Text>
      <ActivityIndicator
        size="large"
        color="#FF6B35"
        style={styles.splashLoader}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  splash: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f8f9fa",
  },
  splashTitle: {
    fontSize: 36,
    fontWeight: "bold",
    color: "#FF6B35",
    marginBottom: 24,
  },
  splashLoader: { marginTop: 16 },
});

export default AppNavigator;
export type { RootStackParams, AuthStackParams, MainTabParams };
