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

import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import React, { useEffect } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { restoreAuth } from "../hooks/useAuth";
import useColorTheme from "../hooks/useColorTheme";
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

/** Auth-gated root navigator. */
function AppNavigator(): React.JSX.Element {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isInitialized = useAuthStore((s) => s.isInitialized);
  const { navTheme, colors } = useColorTheme();

  useEffect(() => {
    void restoreAuth();
  }, []);

  if (!isInitialized) {
    return <SplashLoading colors={colors} />;
  }

  return (
    <NavigationContainer theme={navTheme}>
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
  const { colors } = useColorTheme();

  return (
    <MainTab.Navigator
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textTertiary,
        tabBarStyle: { backgroundColor: colors.card },
        headerStyle: { backgroundColor: colors.primary },
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
function SplashLoading(props: {
  colors: { primary: string; background: string };
}): React.JSX.Element {
  return (
    <View style={[styles.splash, { backgroundColor: props.colors.background }]}>
      <Text style={[styles.splashTitle, { color: props.colors.primary }]}>
        BuzzReach
      </Text>
      <ActivityIndicator
        size="large"
        color={props.colors.primary}
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
  },
  splashTitle: {
    fontSize: 36,
    fontWeight: "bold",
    marginBottom: 24,
  },
  splashLoader: { marginTop: 16 },
});

export default AppNavigator;
export type { RootStackParams, AuthStackParams, MainTabParams };
