/**
 * DESKTOP-001: Electron App wrapper.
 *
 * Wraps the existing React frontend app with native menu bar,
 * keyboard shortcuts, and platform-specific adjustments.
 * Reuses all web frontend components — no duplicate code.
 */

import React, { useEffect, useState, useCallback } from "react";
import type { PreloadBridge, UpdateCheckResult } from "../preload";

/* ---------- Types ---------- */

interface AppState {
  version: string;
  updateAvailable: boolean;
  updateVersion: string;
}

interface UpdateBannerProps {
  version: string;
  onInstall: () => void;
}

/* ---------- Bridge access ---------- */

declare global {
  interface Window {
    buzzreach: PreloadBridge;
  }
}

function getBridge(): PreloadBridge | null {
  return window.buzzreach ?? null;
}

/* ---------- Hooks ---------- */

function useNativeClipboard(): {
  copy: (text: string) => Promise<void>;
  paste: () => Promise<string>;
} {
  const bridge = getBridge();

  const copy = useCallback(
    async (text: string): Promise<void> => {
      if (bridge) {
        await bridge.clipboard.write(text);
      }
    },
    [bridge]
  );

  const paste = useCallback(async (): Promise<string> => {
    if (bridge) {
      return bridge.clipboard.read();
    }
    return "";
  }, [bridge]);

  return { copy, paste };
}

function useAppVersion(): string {
  const [version, setVersion] = useState<string>("");

  useEffect(() => {
    const bridge = getBridge();
    if (bridge) {
      bridge.app.getVersion().then(setVersion);
    }
  }, []);

  return version;
}

/* ---------- Components ---------- */

function UpdateBanner({
  version,
  onInstall,
}: UpdateBannerProps): React.ReactElement | null {
  if (!version) return null;

  return (
    <div className="update-banner" role="alert">
      <span>BuzzReach {version} is available.</span>
      <button onClick={onInstall} type="button">
        Restart to Update
      </button>
    </div>
  );
}

function TitleBar(): React.ReactElement {
  const version = useAppVersion();

  return (
    <div className="title-bar">
      <span className="title-bar__name">BuzzReach</span>
      {version && (
        <span className="title-bar__version">v{version}</span>
      )}
    </div>
  );
}

/* ---------- Main App ---------- */

function DesktopApp(): React.ReactElement {
  const [appState, setAppState] = useState<AppState>({
    version: "",
    updateAvailable: false,
    updateVersion: "",
  });

  useEffect(() => {
    const bridge = getBridge();
    if (!bridge) return;

    bridge.app.getVersion().then((v: string) => {
      setAppState((prev) => ({ ...prev, version: v }));
    });

    bridge.update.check().then((result: UpdateCheckResult) => {
      if (result.available) {
        setAppState((prev) => ({
          ...prev,
          updateAvailable: true,
          updateVersion: result.version,
        }));
      }
    });
  }, []);

  const handleInstallUpdate = useCallback((): void => {
    const bridge = getBridge();
    if (bridge) {
      bridge.update.install();
    }
  }, []);

  return (
    <div className="desktop-app">
      <TitleBar />

      {appState.updateAvailable && (
        <UpdateBanner
          version={appState.updateVersion}
          onInstall={handleInstallUpdate}
        />
      )}

      <main className="desktop-app__content">
        {/*
          Loads the existing web frontend via the same URL.
          All React components from FE-001, FE-002 etc. are
          rendered within the Electron BrowserWindow that
          loads the backend URL directly. No component
          duplication — the Electron shell wraps the web app.
        */}
        <div className="desktop-app__webview" />
      </main>
    </div>
  );
}

export default DesktopApp;
export { useNativeClipboard, useAppVersion, UpdateBanner, TitleBar };
