/**
 * DESKTOP-001: Electron main process.
 *
 * Manages window creation, native menus, system tray,
 * and IPC handlers for native OS integration.
 *
 * Security: contextIsolation=true, nodeIntegration=false,
 * sandbox=true. All renderer communication via preload bridge.
 */

import {
  app,
  BrowserWindow,
  Menu,
  Tray,
  nativeImage,
  globalShortcut,
} from "electron";
import path from "path";
import { registerIpcHandlers } from "./ipcHandlers";
import { createAutoUpdater } from "./autoUpdate";

/* ---------- Type exports ---------- */

export interface WebPreferences {
  preload: string;
  contextIsolation: boolean;
  nodeIntegration: boolean;
  sandbox: boolean;
}

export interface ElectronWindowConfig {
  width: number;
  height: number;
  minWidth: number;
  minHeight: number;
  title: string;
  webPreferences: WebPreferences;
}

export interface MenuItem {
  label?: string;
  accelerator?: string;
  type?: "separator";
  isDefault?: boolean;
  click?: () => void;
  submenu?: MenuItem[];
}

export interface MenuTemplate {
  items: MenuItem[];
}

export interface TrayConfig {
  tooltip: string;
  menuItems: MenuItem[];
}

/* ---------- Window defaults ---------- */

function getWindowConfig(): ElectronWindowConfig {
  return {
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: "BuzzReach",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  };
}

/* ---------- Menu ---------- */

function buildMenuTemplate(win: BrowserWindow): MenuTemplate {
  return {
    items: [
      {
        label: "File",
        submenu: [
          {
            label: "Preferences",
            accelerator: "CmdOrCtrl+,",
            click: () => win.webContents.send("navigate", "/settings"),
          },
          { type: "separator" },
          {
            label: "Quit",
            accelerator: "CmdOrCtrl+Q",
            click: () => app.quit(),
          },
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
          {
            label: "Check for Updates",
            click: () => win.webContents.send("update:check-manual"),
          },
          {
            label: "About BuzzReach",
            click: () => win.webContents.send("navigate", "/about"),
          },
        ],
      },
    ],
  };
}

/* ---------- Tray ---------- */

function buildTrayConfig(): TrayConfig {
  return {
    tooltip: "BuzzReach",
    menuItems: [
      {
        label: "Open BuzzReach",
        isDefault: true,
        click: () => BrowserWindow.getAllWindows()[0]?.show(),
      },
      { type: "separator" },
      { label: "Check for Updates" },
      {
        label: "Quit BuzzReach",
        click: () => app.quit(),
      },
    ],
  };
}

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;

/* ---------- Window creation ---------- */

function createMainWindow(): BrowserWindow {
  const config = getWindowConfig();
  const win = new BrowserWindow(config);

  const menuTemplate = buildMenuTemplate(win);
  const menu = Menu.buildFromTemplate(
    menuTemplate.items as Electron.MenuItemConstructorOptions[]
  );
  Menu.setApplicationMenu(menu);

  const appUrl = process.env.BUZZREACH_URL || "http://localhost:8000";
  win.loadURL(appUrl);

  win.on("closed", () => {
    mainWindow = null;
  });

  return win;
}

/* ---------- Tray creation ---------- */

function createTray(): Tray {
  const iconPath = path.join(__dirname, "assets", "icon.png");
  const icon = nativeImage.createFromPath(iconPath);
  const systemTray = new Tray(icon);

  const trayConfig = buildTrayConfig();
  const contextMenu = Menu.buildFromTemplate(
    trayConfig.menuItems as Electron.MenuItemConstructorOptions[]
  );

  systemTray.setToolTip(trayConfig.tooltip);
  systemTray.setContextMenu(contextMenu);

  systemTray.on("click", () => {
    mainWindow?.show();
  });

  return systemTray;
}

/* ---------- Keyboard shortcuts ---------- */

function registerShortcuts(win: BrowserWindow): void {
  globalShortcut.register("CmdOrCtrl+W", () => {
    win.close();
  });

  globalShortcut.register("CmdOrCtrl+R", () => {
    win.reload();
  });
}

/* ---------- App lifecycle ---------- */

app.whenReady().then(() => {
  registerIpcHandlers();
  mainWindow = createMainWindow();
  tray = createTray();
  registerShortcuts(mainWindow);
  createAutoUpdater(mainWindow);

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createMainWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});
