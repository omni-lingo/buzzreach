/**
 * DESKTOP-001: Native OS integration type contracts.
 *
 * Defines the interfaces for native clipboard, file dialogs,
 * and system notifications used by the preload bridge
 * and consumed by the renderer process.
 */

/* ---------- Clipboard ---------- */

export interface NativeClipboard {
  readText: () => Promise<string>;
  writeText: (text: string) => Promise<boolean>;
  readHTML: () => Promise<string>;
  clear: () => Promise<boolean>;
}

/* ---------- Dialogs ---------- */

export interface OpenDialogOptions {
  title?: string;
  defaultPath?: string;
  filters?: FileFilter[];
  properties?: DialogProperty[];
}

export interface SaveDialogOptions {
  title?: string;
  defaultPath?: string;
  filters?: FileFilter[];
}

export interface MessageBoxOptions {
  type?: "none" | "info" | "error" | "question" | "warning";
  title?: string;
  message: string;
  buttons?: string[];
}

export interface FileFilter {
  name: string;
  extensions: string[];
}

export type DialogProperty =
  | "openFile"
  | "openDirectory"
  | "multiSelections";

export interface OpenDialogResult {
  canceled: boolean;
  filePaths: string[];
}

export interface SaveDialogResult {
  canceled: boolean;
  filePath: string | null;
}

export interface MessageBoxResult {
  response: number;
}

export interface NativeDialogs {
  showOpenDialog: (
    opts: OpenDialogOptions
  ) => Promise<OpenDialogResult>;
  showSaveDialog: (
    opts: SaveDialogOptions
  ) => Promise<SaveDialogResult>;
  showMessageBox: (
    opts: MessageBoxOptions
  ) => Promise<MessageBoxResult>;
}

/* ---------- Notifications ---------- */

export interface NotificationOptions {
  title: string;
  body: string;
  icon?: string;
  urgency?: "low" | "normal" | "critical";
  silent?: boolean;
}

export interface NativeNotifications {
  show: (opts: NotificationOptions) => Promise<string>;
  isSupported: () => boolean;
}

/* ---------- Platform detection ---------- */

export type Platform = "win32" | "darwin" | "linux";

export function getPlatformFeatures(platform: Platform): {
  hasTray: boolean;
  hasDockMenu: boolean;
  hasTaskbar: boolean;
  notificationApi: "native" | "electron";
} {
  switch (platform) {
    case "win32":
      return {
        hasTray: true,
        hasDockMenu: false,
        hasTaskbar: true,
        notificationApi: "native",
      };
    case "darwin":
      return {
        hasTray: true,
        hasDockMenu: true,
        hasTaskbar: false,
        notificationApi: "native",
      };
    case "linux":
      return {
        hasTray: true,
        hasDockMenu: false,
        hasTaskbar: false,
        notificationApi: "electron",
      };
  }
}
