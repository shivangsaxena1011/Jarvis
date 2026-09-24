# SHIVANI — Mobile Setup & Physical Device Guide

This guide walks you through building, installing, and pairing **SHIVANI MOBILE** on an Android phone or emulator.

---

## 1. Prerequisites

- **Android Device / Emulator**: Running Android 9.0+ (API Level 28+). Android 14+ recommended.
- **Android Studio**: Android Studio Hedgehog / Iguana / Jellyfish with JDK 17.
- **USB Cable** or common Wi-Fi network with your laptop.

---

## 2. Build and Install App

### Option A: Using Android Studio
1. Open the project folder `apps/mobile/` in Android Studio.
2. Allow Gradle sync to complete dependencies (`androidx.compose`, `okhttp3`, `security-crypto`).
3. Connect your Android phone with **USB Debugging** enabled in Developer Options.
4. Click **Run 'app'** (or press `Shift + F10`) to compile and install on your device.

### Option B: Using Gradle CLI
```bash
cd apps/mobile
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

---

## 3. Enable Required Permissions

Once installed on the phone:
1. **Launch SHIVANI MOBILE**.
2. Tap the **Perms** tab in the bottom navigation.
3. Tap **Enable** next to **Accessibility Service**:
   - The app will redirect you to Android System Accessibility Settings.
   - Tap **Installed Apps** ──▶ **SHIVANI MOBILE** ──▶ Toggle **Use SHIVANI MOBILE** ON.
4. Grant **Photos & Media** access when prompted so SHIVANI can locate hackathon/project images.

---

## 4. Pairing with Laptop

1. Ensure both devices are on the same Wi-Fi network, or connect via USB and forward the port:
   ```bash
   adb reverse tcp:8765 tcp:8765
   ```
2. On your laptop, run SHIVANI:
   ```powershell
   .venv\Scripts\python.exe main.py
   ```
3. In SHIVANI Desktop (or via CLI task):
   - The pairing code is displayed (e.g. `492817`).
4. In **SHIVANI MOBILE**:
   - Tap the **Pair** tab.
   - Enter your laptop's IP address (or `127.0.0.1` if using `adb reverse`).
   - Enter the 6-digit pairing code.
   - Tap **Approve & Connect**.
5. The Home screen will immediately update to **● Connected**.

---

## 5. Troubleshooting

- **Device shows "Disconnected"**:
  - Verify that the laptop firewall allows inbound traffic on port `8765`.
  - If using USB, run `adb reverse tcp:8765 tcp:8765` again.
- **App commands fail with "Accessibility not enabled"**:
  - Open System Settings ──▶ Accessibility ──▶ Ensure SHIVANI service is ON.
- **Background disconnects**:
  - Go to App Info ──▶ Battery ──▶ Set to **Unrestricted** so Android does not kill the foreground keepalive service.
