# ATOM: DESKTOP-001 — Electron Desktop App (Windows, macOS, Linux)

**Layer:** L4
**Module:** desktop
**Effort:** M
**Depends on:** mobile

## Inputs (what this atom reads/consumes)
- React components from frontend (FE-001, FE-002, etc.)
- Electron framework
- Native OS APIs (clipboard, notifications, file system)

## Outputs (what this atom produces)
- `src/desktop/` — Electron app:
  - `main.ts` — Electron main process (window management)
  - `preload.ts` — secure IPC bridge
  - Reuses React frontend code (same components as web app)
  - Platform-specific adjustments:
    - Windows: taskbar icon, tray menu
    - macOS: dock menu, native notifications
    - Linux: system tray
- `src/desktop/src/App.tsx` — Electron wrapper:
  - Wraps existing frontend app
  - Adds native menu bar (File, Edit, Help)
  - Menu items: Open Settings, Check for Updates, Quit
  - Keyboard shortcuts: Cmd+W (close window), Cmd+, (settings)
- Native integrations:
  - Clipboard (native API faster than browser)
  - File dialogs (save/open files)
  - System notifications (vs browser push)
  - Tray menu (quick access)
- Auto-update mechanism:
  - Check for new version on startup
  - Download + install in background
  - Notify user + apply on next launch
- `src/desktop/package.json` — build config (electron-builder)
- `src/desktop/build/` — installers:
  - Windows: .exe installer
  - macOS: .dmg
  - Linux: .AppImage
- `tests/test_electron.tsx` — render, native APIs

## Acceptance criteria
- [ ] App launches and displays login screen
- [ ] Reuses web frontend components (no duplicate code)
- [ ] Clipboard copy works natively (faster than browser)
- [ ] System notifications show (native API)
- [ ] Tray menu available (Windows/macOS/Linux)
- [ ] Settings accessible (Cmd+, or File → Preferences)
- [ ] Auto-update mechanism works
- [ ] Installer signed (prevents security warnings)
- [ ] Notarized on macOS (passes security checks)
- [ ] Performance: app launches in <2 seconds

## Cross-module contracts
- Reuses React frontend (FE-001, FE-002, etc.)
- Calls same backend API (API-001)
- Uses same auth flow (AUTH-002)
- Optional: different notification strategy (native vs push)
