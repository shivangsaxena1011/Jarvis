# Android Companion Bridge — SHIVANI Mobile

The mobile companion application allows the laptop SHIVANI agent to control and query the user's paired Android smartphone.

---

## 1. Architecture

```
Laptop SHIVANI
    │
    ▼ (Mutual TLS / Authenticated WebSocket over USB / Wi-Fi)
Android Companion Service (Shivani Mobile)
    │
    ▼ (Android Accessibility API / UIAutomator)
Target App (e.g. Instagram, WhatsApp, Gallery)
```

---

## 2. Pairing & Security Flow
1. Laptop generates a high-entropy 6-digit numeric pairing challenge.
2. User enters the pairing code into the **Shivani Mobile** app on Android.
3. Cryptographic handshake generates a shared device token stored securely in Android Keystore and the local credential vault.
4. Subsequent sessions authenticate over mutual signature challenge.

---

## 3. Supported Mobile Operations
- `android.launch_app`: Launch target application by package name.
- `android.screenshot`: Screen capture for vision analysis.
- `android.tap`: Click button by UI text or coordinate.
- `android.type`: Input text into active field.
- `android.swipe`: Scroll feeds or navigate pages.
- `android.read_notifications`: Permitted notification parsing.
