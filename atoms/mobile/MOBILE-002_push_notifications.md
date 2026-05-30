# ATOM: MOBILE-002 — Push Notifications (iOS/Android)

**Layer:** L3/L4
**Module:** mobile
**Effort:** M
**Depends on:** MOBILE-001, BILL-002

## Inputs (what this atom reads/consumes)
- Expo Push Notifications service
- Firebase Cloud Messaging (FCM) for Android
- Apple Push Notification service (APNs) for iOS

## Outputs (what this atom produces)
- `src/mobile/src/services/pushNotifications.ts` — Expo notifications setup:
  - `registerForPushNotificationsAsync()` → get device token
  - `handleNotificationResponse()` → navigate to opportunity when tapped
  - Foreground vs background notification handlers
- `src/backend/services/push_service.py`:
  - `send_push_notification(user_id, title, body, opportunity_id)` → POST to Expo Push API
  - `batch_send_notifications(user_ids, message)` → bulk send
  - `schedule_notification(user_id, message, datetime)` → send at specific time
- `src/backend/models/push_subscription.py` — store device tokens:
  - `id`, `user_id`, `device_token`, `platform` (ios/android)
  - `is_active`, `created_at`, `updated_at`
- `src/backend/api/push.py` — routes:
  - POST `/api/v1/push/register` — client sends device token
  - POST `/api/v1/push/unregister` — mark token inactive
- Backend job (JOB-001 expansion):
  - When new high-scoring opportunity created → send push to relevant users
  - Frequency: respect user preference (hourly digest, daily, or real-time)
- `tests/test_push_notifications.py` — mock Expo Push API

## Acceptance criteria
- [ ] App requests push notification permission on first launch
- [ ] Device token stored in DB after registration
- [ ] User receives push when new opportunity discovered (if opted in)
- [ ] Notification includes: opportunity title, score, platform
- [ ] Tapping notification opens app → navigates to that opportunity
- [ ] Users can disable notifications in settings (FE-001)
- [ ] Old/stale device tokens cleaned up (via Expo feedback API)
- [ ] No push sent to unverified users
- [ ] Plan limits respected: free = daily digest only, pro/premium = real-time

## Cross-module contracts
- Reads Opportunity events (PIPE-001)
- Updates Device token table
- Respects user preferences (FE-001)
- Integrates with plan limits (BILL-002)
