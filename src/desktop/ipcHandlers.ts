/**
 * DESKTOP-001: Main-process IPC handlers.
 *
 * Registers handlers for each whitelisted IPC channel.
 * Runs in the main process — has full Node.js access.
 * The preload bridge forwards renderer calls here.
 */

import {
  app,
  ipcMain,
  clipboard,
  dialog,
  Notification,
  BrowserWindow,
} from "electron";

/* ---------- Registration ---------- */

export function registerIpcHandlers(): void {
  ipcMain.handle("clipboard:read", () => {
    return clipboard.readText();
  });

  ipcMain.handle("clipboard:write", (_event, text: string) => {
    clipboard.writeText(text);
    return true;
  });

  ipcMain.handle("dialog:open", async () => {
    const win = BrowserWindow.getFocusedWindow();
    if (!win) return null;
    const result = await dialog.showOpenDialog(win, {
      properties: ["openFile"],
    });
    return result.canceled ? null : result.filePaths[0] ?? null;
  });

  ipcMain.handle("dialog:save", async () => {
    const win = BrowserWindow.getFocusedWindow();
    if (!win) return null;
    const result = await dialog.showSaveDialog(win, {});
    return result.canceled ? null : result.filePath ?? null;
  });

  ipcMain.handle(
    "notification:show",
    (_event, title: string, body: string) => {
      if (!Notification.isSupported()) return false;
      new Notification({ title, body }).show();
      return true;
    }
  );

  ipcMain.handle(
    "tray:update-badge",
    (_event, count: number) => {
      if (process.platform === "darwin") {
        app.setBadgeCount(count);
      }
      return true;
    }
  );

  ipcMain.handle("app:get-version", () => {
    return app.getVersion();
  });
}
