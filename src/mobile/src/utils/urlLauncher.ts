/**
 * URL launcher utility for opening threads in browser/app (MOBILE-004).
 *
 * Provides:
 * - openThread: opens URL in native browser
 * - openInRedditApp: opens Reddit URL in app (if installed) or browser
 *
 * Uses expo-linking which:
 * - Preserves user's logged-in session (opens in default browser)
 * - Returns to BuzzReach app on back button (standard OS behavior)
 * - No network calls needed from this utility
 *
 * Cross-module contracts:
 * - Consumed by OpportunityActions component (MOBILE-004)
 * - Uses OpportunityData.url from contracts/opportunity/opportunity.py
 */

import * as Linking from "expo-linking";

const REDDIT_SCHEME = "reddit://";

/**
 * Open a URL in the device's native browser.
 * Returns true on success, false on failure.
 */
async function openThread(url: string): Promise<boolean> {
  try {
    await Linking.openURL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Convert a Reddit HTTPS URL to a reddit:// deep link.
 * Replaces https:// with reddit:// to trigger the Reddit app.
 */
function toRedditDeepLink(url: string): string {
  return url.replace(/^https?:\/\//, REDDIT_SCHEME);
}

/**
 * Open a Reddit URL in the Reddit app (if installed) or browser.
 *
 * Checks if the device can handle the reddit:// scheme.
 * Falls back to browser if the Reddit app is not installed.
 * Returns true on success, false on failure.
 */
async function openInRedditApp(url: string): Promise<boolean> {
  try {
    const deepLink = toRedditDeepLink(url);
    const canOpen = await Linking.canOpenURL(deepLink);

    if (canOpen) {
      await Linking.openURL(deepLink);
    } else {
      await Linking.openURL(url);
    }
    return true;
  } catch {
    return false;
  }
}

export { openInRedditApp, openThread, toRedditDeepLink };
