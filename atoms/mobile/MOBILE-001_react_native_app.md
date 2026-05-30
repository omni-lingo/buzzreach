# ATOM: MOBILE-001 — Mobile App (React Native) Base Setup

**Layer:** L4
**Module:** mobile
**Effort:** M
**Depends on:** API-001, ONBOARD-001

## Inputs (what this atom reads/consumes)
- Backend API endpoints (auth, opportunities)
- React Native CLI + Expo
- iOS/Android SDK requirements

## Outputs (what this atom produces)
- `src/mobile/` — React Native project structure:
  - `app.json` (Expo config)
  - `package.json` with dependencies (expo, react-native, @react-native-community/*, etc.)
  - `tsconfig.json` for TypeScript support
- `src/mobile/src/screens/LoginScreen.tsx` — login via API key or username/password
- `src/mobile/src/screens/FeedScreen.tsx` — main feed (stub, full impl in MOBILE-003)
- `src/mobile/src/screens/SettingsScreen.tsx` — basic settings (stub)
- `src/mobile/src/api/client.ts` — API client wrapper (axios + auth interceptors)
- `src/mobile/src/hooks/useAuth.ts` — auth context + login/logout
- `src/mobile/src/store/` — Redux or Zustand for state (opportunities, user, settings)
- `.eas.json` — Expo Application Services config for building/publishing
- `src/mobile/eas.json` — publish targets (iOS, Android)
- `tests/mobile/app.test.tsx` — basic render test

## Acceptance criteria
- [ ] App runs on iOS simulator (Xcode) and Android emulator
- [ ] User can login via API key from settings page
- [ ] Auth token persisted securely (AsyncStorage + encryption)
- [ ] Basic navigation between Login → Feed → Settings screens
- [ ] API calls include JWT in Authorization header
- [ ] App builds without errors (eas build --platform ios/android)
- [ ] Splash screen shows while loading auth state
- [ ] Logout clears stored token

## Cross-module contracts
- Uses `UserData`, `OpportunityEvent` contracts
- Calls API-001 authenticated endpoints
- Integrates with MOBILE-002 (push notifications)
