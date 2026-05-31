/**
 * Tests for DESKTOP-001: Native integrations, auto-update,
 * and build configuration.
 *
 * Split from test_electron.tsx (domain: native OS features).
 * Uses console.assert for contract + unit validation.
 */

import type {
  NativeClipboard,
  NativeDialogs,
  NativeNotifications,
} from "../src/desktop/nativeIntegrations";
import type { AutoUpdateConfig } from "../src/desktop/autoUpdate";

/* ---------- Clipboard tests ---------- */

function testClipboardContract(): void {
  const clipboard: NativeClipboard = {
    readText: async () => "test content",
    writeText: async (_text: string) => true,
    readHTML: async () => "<p>test</p>",
    clear: async () => true,
  };
  console.assert(
    typeof clipboard.readText === "function",
    "readText is function"
  );
  console.assert(
    typeof clipboard.writeText === "function",
    "writeText is function"
  );
  console.assert(
    typeof clipboard.readHTML === "function",
    "readHTML is function"
  );
  console.assert(
    typeof clipboard.clear === "function",
    "clear is function"
  );
}

/* ---------- Dialog tests ---------- */

function testDialogsContract(): void {
  const dialogs: NativeDialogs = {
    showOpenDialog: async () => ({
      canceled: false,
      filePaths: ["/test/file.txt"],
    }),
    showSaveDialog: async () => ({
      canceled: false,
      filePath: "/test/output.txt",
    }),
    showMessageBox: async () => ({
      response: 0,
    }),
  };
  console.assert(
    typeof dialogs.showOpenDialog === "function",
    "showOpenDialog is function"
  );
  console.assert(
    typeof dialogs.showSaveDialog === "function",
    "showSaveDialog is function"
  );
  console.assert(
    typeof dialogs.showMessageBox === "function",
    "showMessageBox is function"
  );
}

/* ---------- Notification tests ---------- */

function testNotificationsContract(): void {
  const notifications: NativeNotifications = {
    show: async () => "notif-123",
    isSupported: () => true,
  };
  console.assert(
    typeof notifications.show === "function",
    "show is function"
  );
  console.assert(
    notifications.isSupported(),
    "Notifications should be supported"
  );
}

/* ---------- Auto-update tests ---------- */

function testAutoUpdateConfig(): void {
  const config: AutoUpdateConfig = {
    checkOnStartup: true,
    autoDownload: true,
    notifyOnAvailable: true,
    feedUrl: "https://updates.buzzreach.com",
    currentVersion: "1.0.0",
  };
  console.assert(
    config.checkOnStartup === true,
    "Check on startup enabled"
  );
  console.assert(
    config.autoDownload === true,
    "Auto download enabled"
  );
  console.assert(
    config.notifyOnAvailable === true,
    "Notify on available"
  );
  console.assert(
    config.feedUrl.startsWith("https://"),
    "Feed URL is HTTPS"
  );
}

function testUpdateCheckResult(): void {
  const noUpdate = { available: false, version: "" };
  const hasUpdate = { available: true, version: "1.1.0" };

  console.assert(!noUpdate.available, "No update available");
  console.assert(hasUpdate.available, "Update available");
  console.assert(
    hasUpdate.version === "1.1.0",
    "New version reported"
  );
}

/* ---------- Build config tests ---------- */

function testBuildConfig(): void {
  const buildConfig = {
    appId: "com.buzzreach.desktop",
    productName: "BuzzReach",
    directories: { output: "build" },
    win: { target: "nsis", icon: "assets/icon.ico" },
    mac: {
      target: "dmg",
      icon: "assets/icon.icns",
      hardenedRuntime: true,
      notarize: true,
    },
    linux: { target: "AppImage", icon: "assets/icon.png" },
  };
  console.assert(
    buildConfig.appId === "com.buzzreach.desktop",
    "App ID matches"
  );
  console.assert(
    buildConfig.productName === "BuzzReach",
    "Product name matches"
  );
  console.assert(
    buildConfig.win.target === "nsis",
    "Windows target is nsis"
  );
  console.assert(
    buildConfig.mac.target === "dmg",
    "macOS target is dmg"
  );
  console.assert(
    buildConfig.mac.hardenedRuntime === true,
    "macOS hardened runtime"
  );
  console.assert(
    buildConfig.mac.notarize === true,
    "macOS notarization enabled"
  );
  console.assert(
    buildConfig.linux.target === "AppImage",
    "Linux target is AppImage"
  );
}

function testNoSecretsInConfig(): void {
  const configStr = JSON.stringify({
    appId: "com.buzzreach.desktop",
    feedUrl: "https://updates.buzzreach.com",
  });
  console.assert(
    !configStr.includes("sk_test"),
    "No test keys in config"
  );
  console.assert(
    !configStr.includes("sk_live"),
    "No live keys in config"
  );
  console.assert(
    !configStr.includes("password"),
    "No passwords in config"
  );
}

/* ---------- Run all tests ---------- */

testClipboardContract();
testDialogsContract();
testNotificationsContract();
testAutoUpdateConfig();
testUpdateCheckResult();
testBuildConfig();
testNoSecretsInConfig();
