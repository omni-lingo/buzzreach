/**
 * Push Notifications service for Expo (MOBILE-002).
 *
 * Handles:
 * - Permission requests and device token registration
 * - Foreground and background notification handlers
 * - Notification tap → navigate to opportunity
 *
 * Cross-module contracts:
 * - Calls POST /api/v1/push/register and /unregister
 * - Reads opportunity_id from notification data for deep linking
 */

import Constants from "expo-constants";
import * as Device from "expo-device";
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

const API_BASE_URL =
  Constants.expoConfig?.extra?.apiBaseUrl ?? "http://localhost:8000";

/** Result of push token registration attempt. */
interface RegistrationResult {
  success: boolean;
  token: string | null;
  error: string | null;
}

/** Callback type for navigation on notification tap. */
type NavigateToOpportunity = (opportunityId: string) => void;

/**
 * Configure default notification behavior for foreground display.
 * Must be called once at app startup.
 */
function configureForegroundHandler(): void {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: true,
    }),
  });
}

/**
 * Request push notification permissions and register the device token
 * with the BuzzReach backend.
 *
 * @param authToken - JWT token for authenticated API calls
 * @returns Registration result with token or error
 */
async function registerForPushNotificationsAsync(
  authToken: string
): Promise<RegistrationResult> {
  if (!Device.isDevice) {
    return {
      success: false,
      token: null,
      error: "Push notifications require a physical device",
    };
  }

  const { status: existingStatus } =
    await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") {
    return {
      success: false,
      token: null,
      error: "Push notification permission denied",
    };
  }

  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const pushToken = await Notifications.getExpoPushTokenAsync({
    projectId,
  });
  const token = pushToken.data;

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "Default",
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: "#FF6B35",
    });
  }

  const registered = await postTokenToBackend(token, authToken);
  if (!registered) {
    return { success: false, token, error: "Failed to register with server" };
  }

  return { success: true, token, error: null };
}

/**
 * Set up a listener that fires when the user taps a notification.
 * Navigates to the relevant opportunity screen.
 *
 * @param onNavigate - Callback to handle navigation
 * @returns Subscription that should be cleaned up on unmount
 */
function handleNotificationResponse(
  onNavigate: NavigateToOpportunity
): Notifications.Subscription {
  return Notifications.addNotificationResponseReceivedListener(
    (response) => {
      const data = response.notification.request.content.data;
      const opportunityId = data?.opportunity_id;
      if (typeof opportunityId === "string" && opportunityId.length > 0) {
        onNavigate(opportunityId);
      }
    }
  );
}

/**
 * Set up a listener for notifications received while app is in foreground.
 *
 * @param onReceive - Callback with the notification object
 * @returns Subscription that should be cleaned up on unmount
 */
function addForegroundListener(
  onReceive: (notification: Notifications.Notification) => void
): Notifications.Subscription {
  return Notifications.addNotificationReceivedListener(onReceive);
}

/**
 * Unregister the device token from the backend.
 *
 * @param token - The Expo push token to unregister
 * @param authToken - JWT token for authenticated API calls
 */
async function unregisterPushToken(
  token: string,
  authToken: string
): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/push/unregister`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify({ device_token: token }),
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * POST the device token to the BuzzReach backend for registration.
 */
async function postTokenToBackend(
  token: string,
  authToken: string
): Promise<boolean> {
  const platform = Platform.OS === "ios" ? "ios" : "android";
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/push/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify({ device_token: token, platform }),
    });
    return response.ok;
  } catch {
    return false;
  }
}

export {
  configureForegroundHandler,
  registerForPushNotificationsAsync,
  handleNotificationResponse,
  addForegroundListener,
  unregisterPushToken,
};

export type { RegistrationResult, NavigateToOpportunity };
