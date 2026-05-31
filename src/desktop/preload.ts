/**
 * DESKTOP-001: Preload script — secure IPC bridge.
 *
 * Runs in the renderer process with limited privileges.
 * Exposes a typed API via contextBridge. Only whitelisted
 * IPC channels are allowed. No Node.js APIs leak.
 */

import { contextBridge, ipcRenderer } from "electron";

/* ---------- Type exports ---------- */

export type IpcChannel =
  | "clipboard:read"
  | "clipboard:write"
  | "dialog:open"
  | "dialog:save"
  | "notification:show"
  | "tray:update-badge"
  | "update:check"
  | "update:download"
  | "update:install"
  | "app:get-version";

export interface UpdateCheckResult {
  available: boolean;
  version: string;
}

export interface PreloadBridge {
  clipboard: {
    read: () => Promise<string>;
    write: (text: string) => Promise<boolean>;
  };
  dialog: {
    open: () => Promise<string | null>;
    save: () => Promise<string | null>;
  };
  notification: {
    show: (title: string, body: string) => Promise<boolean>;
  };
  tray: {
    updateBadge: (count: number) => Promise<boolean>;
  };
  update: {
    check: () => Promise<UpdateCheckResult>;
    download: () => Promise<boolean>;
    install: () => Promise<void>;
  };
  app: {
    getVersion: () => Promise<string>;
  };
}

/* ---------- Channel allowlist ---------- */

const ALLOWED_CHANNELS: ReadonlySet<IpcChannel> = new Set([
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
]);

export function isAllowedChannel(
  channel: string
): channel is IpcChannel {
  return ALLOWED_CHANNELS.has(channel as IpcChannel);
}

/* ---------- Renderer-side bridge ---------- */

const bridge: PreloadBridge = {
  clipboard: {
    read: () => ipcRenderer.invoke("clipboard:read"),
    write: (text: string) =>
      ipcRenderer.invoke("clipboard:write", text),
  },
  dialog: {
    open: () => ipcRenderer.invoke("dialog:open"),
    save: () => ipcRenderer.invoke("dialog:save"),
  },
  notification: {
    show: (title: string, body: string) =>
      ipcRenderer.invoke("notification:show", title, body),
  },
  tray: {
    updateBadge: (count: number) =>
      ipcRenderer.invoke("tray:update-badge", count),
  },
  update: {
    check: () => ipcRenderer.invoke("update:check"),
    download: () => ipcRenderer.invoke("update:download"),
    install: () => ipcRenderer.invoke("update:install"),
  },
  app: {
    getVersion: () => ipcRenderer.invoke("app:get-version"),
  },
};

contextBridge.exposeInMainWorld("buzzreach", bridge);
