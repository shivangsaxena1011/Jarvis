# SHIVANI — Secure Device Bridge Architecture

The SHIVANI Secure Device Bridge establishes an encrypted, mutually authenticated bidirectional control and telemetry channel between the laptop orchestrator and paired Android companion nodes.

---

## 1. Network & Transport Layer

- **Primary Transport**: Authenticated WebSocket / TLS over trusted Local Area Network (Wi-Fi) or direct USB reverse tethering (`adb reverse tcp:8765 tcp:8765`).
- **Default Port**: `8765`.
- **Keepalive Protocol**: Periodic ping/pong heartbeat (every 15–30 seconds) ensuring the orchestrator detects offline or out-of-range phones immediately.
- **Fail-Safe Disconnect**: If the connection drops or heartbeat exceeds the threshold, the device state transitions to `DEVICE_DISCONNECTED`. Any pending phone task is aborted rather than blindly executed.

---

## 2. Cryptographic Handshake & Pairing Flow

Pairing strictly requires explicit user confirmation on both sides:

```
1. Laptop SHIVANI initiates pairing:
   - Generates high-entropy 6-digit numeric challenge code (e.g. "492817").
   - Starts 5-minute ephemeral pairing session.

2. Android Phone (SHIVANI MOBILE):
   - User inputs 6-digit code into Connection Screen.
   - Screen displays prompt: "Pair with this computer? (Shivani Desktop)".
   - User taps [Approve & Connect].

3. Token Exchange:
   - Shared secret token generated via SHA-256 HMAC.
   - Stored securely in Android Keystore on mobile.
   - Stored in local credential vault on laptop.
   - Subsequent sessions authenticate using constant-time HMAC signature verification.
```

---

## 3. Structured Command Protocol

Every command transmitted between laptop and phone adheres to a strict correlation schema:

### Command Request
```json
{
  "request_id": "req-9a8b7c6d5e4f",
  "device_id": "shivani-android-001",
  "action": "launch_app",
  "parameters": {
    "package": "com.instagram.android"
  },
  "timestamp": 1727164800.0
}
```

### Command Response
```json
{
  "request_id": "req-9a8b7c6d5e4f",
  "device_id": "shivani-android-001",
  "success": true,
  "result": {
    "package": "com.instagram.android",
    "activity": "com.instagram.android.MainActivity",
    "app_name": "Instagram",
    "status": "launched_and_verified"
  },
  "error": null,
  "execution_time_ms": 142.5
}
```

---

## 4. Emergency Cancellation ("Shivani stop")

When the user triggers an emergency stop ("Shivani stop", Desktop Stop All button, or REST API `/api/emergency/stop`):
1. The laptop orchestrator issues `cancel_task` to the active device.
2. The phone's `UIAutomationManager` and `AccessibilityService` abort pending gestures.
3. The on-device `ActivityLogger` records: `10:43 PM Task cancelled`.
