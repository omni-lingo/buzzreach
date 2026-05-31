/**
 * DESKTOP-001: Auto-update mechanism.
 *
 * Checks for updates on startup, downloads in background,
 * and notifies the user to install on next launch.
 * Uses electron-updater for signed binary distribution.
 */

import { autoUpdater } from "electron-updater";
import { BrowserWindow, Notification } from "electron";
import { app } from "electron";

/* ---------- Type exports ---------- */

export interface AutoUpdateConfig {
  checkOnStartup: boolean;
  autoDownload: boolean;
  notifyOnAvailable: boolean;
  feedUrl: string;
  currentVersion: string;
}

export interface UpdateStatus {
  checking: boolean;
  available: boolean;
  downloading: boolean;
  downloaded: boolean;
  version: string;
  error: string | null;
}

/* ---------- State ---------- */

let updateStatus: UpdateStatus = {
  checking: false,
  available: false,
  downloading: false,
  downloaded: false,
  version: "",
  error: null,
};

/* ---------- Config ---------- */

function getDefaultConfig(): AutoUpdateConfig {
  return {
    checkOnStartup: true,
    autoDownload: true,
    notifyOnAvailable: true,
    feedUrl: "https://updates.buzzreach.com",
    currentVersion: app.getVersion(),
  };
}

/* ---------- Status ---------- */

export function getUpdateStatus(): UpdateStatus {
  return { ...updateStatus };
}

/* ---------- Notifications ---------- */

function notifyUpdateAvailable(version: string): void {
  if (!Notification.isSupported()) return;
  new Notification({
    title: "Update Available",
    body: `BuzzReach ${version} is available. Downloading...`,
  }).show();
}

function notifyUpdateReady(version: string): void {
  if (!Notification.isSupported()) return;
  new Notification({
    title: "Update Ready",
    body: `BuzzReach ${version} will install on next launch.`,
  }).show();
}

/* ---------- Event handlers ---------- */

function setupEventHandlers(win: BrowserWindow): void {
  autoUpdater.on("checking-for-update", () => {
    updateStatus = { ...updateStatus, checking: true };
    win.webContents.send("update:status", updateStatus);
  });

  autoUpdater.on("update-available", (info) => {
    updateStatus = {
      ...updateStatus,
      checking: false,
      available: true,
      version: info.version,
    };
    win.webContents.send("update:status", updateStatus);
    notifyUpdateAvailable(info.version);
  });

  autoUpdater.on("update-not-available", () => {
    updateStatus = {
      ...updateStatus,
      checking: false,
      available: false,
    };
    win.webContents.send("update:status", updateStatus);
  });

  autoUpdater.on("download-progress", () => {
    updateStatus = { ...updateStatus, downloading: true };
    win.webContents.send("update:status", updateStatus);
  });

  autoUpdater.on("update-downloaded", (info) => {
    updateStatus = {
      ...updateStatus,
      downloading: false,
      downloaded: true,
      version: info.version,
    };
    win.webContents.send("update:status", updateStatus);
    notifyUpdateReady(info.version);
  });

  autoUpdater.on("error", (err) => {
    updateStatus = {
      ...updateStatus,
      checking: false,
      downloading: false,
      error: err.message,
    };
    win.webContents.send("update:status", updateStatus);
  });
}

/* ---------- Public API ---------- */

export function createAutoUpdater(win: BrowserWindow): void {
  const config = getDefaultConfig();

  autoUpdater.autoDownload = config.autoDownload;
  setupEventHandlers(win);

  if (config.checkOnStartup) {
    autoUpdater.checkForUpdates();
  }
}

export async function checkForUpdates(): Promise<boolean> {
  const result = await autoUpdater.checkForUpdates();
  return result?.updateInfo?.version !== app.getVersion();
}

export async function downloadUpdate(): Promise<boolean> {
  await autoUpdater.downloadUpdate();
  return true;
}

export function installUpdate(): void {
  autoUpdater.quitAndInstall(false, true);
}
