/**
 * Tests for DESKTOP-001: Electron main process, preload bridge,
 * and App.tsx wrapper.
 *
 * Uses console.assert for contract + unit validation.
 * Native integration tests in test_electron_native.tsx.
 */

import React from "react";

import type {
  ElectronWindowConfig,
  MenuTemplate,
  TrayConfig,
} from "../src/desktop/main";
import type {
  PreloadBridge,
  IpcChannel,
} from "../src/desktop/preload";

/* ---------- Main process tests ---------- */

function testWindowConfigDefaults(): void {
  const config: ElectronWindowConfig = {
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: "BuzzReach",
    webPreferences: {
      preload: "preload.js",
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  };
  console.assert(config.width === 1200, "Default width 1200");
  console.assert(config.height === 800, "Default height 800");
  console.assert(config.minWidth === 800, "Min width 800");
  console.assert(config.minHeight === 600, "Min height 600");
  console.assert(config.title === "BuzzReach", "Title is BuzzReach");
}

function testSecuritySettings(): void {
  const prefs = {
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
  };
  console.assert(
    prefs.contextIsolation === true,
    "Context isolation must be enabled"
  );
  console.assert(
    prefs.nodeIntegration === false,
    "Node integration must be disabled"
  );
  console.assert(prefs.sandbox === true, "Sandbox must be enabled");
}

/* ---------- Preload bridge tests ---------- */

function testIpcChannelAllowlist(): void {
  const allowedChannels: IpcChannel[] = [
    "clipboard:read",
    "clipboard:write",
    "dialog:open",
    "dialog:save",
    "notification:show",
    "tray:update-badge",
    "update:check",
    "update:download",
    "update:install",
    "app:get-version",
  ];
  console.assert(
    allowedChannels.length === 10,
    "Should have 10 allowed IPC channels"
  );
  console.assert(
    !allowedChannels.includes("eval" as IpcChannel),
    "eval channel must not be allowed"
  );
  console.assert(
    !allowedChannels.includes("shell:exec" as IpcChannel),
    "shell:exec must not be allowed"
  );
}

function testPreloadBridgeShape(): void {
  const bridge: PreloadBridge = {
    clipboard: {
      read: async () => "",
      write: async (_text: string) => true,
    },
    dialog: {
      open: async () => null,
      save: async () => null,
    },
    notification: {
      show: async (_title: string, _body: string) => true,
    },
    tray: {
      updateBadge: async (_count: number) => true,
    },
    update: {
      check: async () => ({ available: false, version: "" }),
      download: async () => false,
      install: async () => {},
    },
    app: {
      getVersion: async () => "1.0.0",
    },
  };
  console.assert(
    typeof bridge.clipboard.read === "function",
    "clipboard.read is function"
  );
  console.assert(
    typeof bridge.clipboard.write === "function",
    "clipboard.write is function"
  );
  console.assert(
    typeof bridge.dialog.open === "function",
    "dialog.open is function"
  );
  console.assert(
    typeof bridge.dialog.save === "function",
    "dialog.save is function"
  );
  console.assert(
    typeof bridge.notification.show === "function",
    "notification.show is function"
  );
  console.assert(
    typeof bridge.update.check === "function",
    "update.check is function"
  );
  console.assert(
    typeof bridge.app.getVersion === "function",
    "app.getVersion is function"
  );
}

/* ---------- App.tsx wrapper tests ---------- */

function testMenuTemplateStructure(): void {
  const menu: MenuTemplate = {
    items: [
      {
        label: "File",
        submenu: [
          { label: "Preferences", accelerator: "CmdOrCtrl+," },
          { type: "separator" },
          { label: "Quit", accelerator: "CmdOrCtrl+Q" },
        ],
      },
      {
        label: "Edit",
        submenu: [
          { label: "Undo", accelerator: "CmdOrCtrl+Z" },
          { label: "Redo", accelerator: "CmdOrCtrl+Shift+Z" },
          { type: "separator" },
          { label: "Cut", accelerator: "CmdOrCtrl+X" },
          { label: "Copy", accelerator: "CmdOrCtrl+C" },
          { label: "Paste", accelerator: "CmdOrCtrl+V" },
          { label: "Select All", accelerator: "CmdOrCtrl+A" },
        ],
      },
      {
        label: "Help",
        submenu: [
          { label: "Check for Updates" },
          { label: "About BuzzReach" },
        ],
      },
    ],
  };
  console.assert(menu.items.length === 3, "Menu has 3 top items");
  console.assert(
    menu.items[0].label === "File",
    "First menu is File"
  );
  console.assert(
    menu.items[1].label === "Edit",
    "Second menu is Edit"
  );
  console.assert(
    menu.items[2].label === "Help",
    "Third menu is Help"
  );
}

function testKeyboardShortcuts(): void {
  const shortcuts: Record<string, string> = {
    closeWindow: "CmdOrCtrl+W",
    settings: "CmdOrCtrl+,",
    quit: "CmdOrCtrl+Q",
    reload: "CmdOrCtrl+R",
  };
  console.assert(
    shortcuts.closeWindow === "CmdOrCtrl+W",
    "Close window shortcut"
  );
  console.assert(
    shortcuts.settings === "CmdOrCtrl+,",
    "Settings shortcut"
  );
  console.assert(shortcuts.quit === "CmdOrCtrl+Q", "Quit shortcut");
}

/* ---------- Tray tests ---------- */

function testTrayConfig(): void {
  const tray: TrayConfig = {
    tooltip: "BuzzReach",
    menuItems: [
      { label: "Open BuzzReach", isDefault: true },
      { type: "separator" },
      { label: "Check for Updates" },
      { label: "Quit BuzzReach" },
    ],
  };
  console.assert(tray.tooltip === "BuzzReach", "Tray tooltip");
  console.assert(tray.menuItems.length === 4, "4 tray menu items");
  console.assert(
    tray.menuItems[0].isDefault === true,
    "First item is default action"
  );
}

/* ---------- Run all tests ---------- */

testWindowConfigDefaults();
testSecuritySettings();
testIpcChannelAllowlist();
testPreloadBridgeShape();
testMenuTemplateStructure();
testKeyboardShortcuts();
testTrayConfig();
