# SHIVANI — Phone Security & Privacy Model

The Android companion node is designed with strict privacy boundaries, data minimization, and user-authorized execution. SHIVANI explicitly rejects surveillance-oriented architectures.

---

## 1. Zero Surveillance Principles

1. **No Continuous Screen Streaming**: Screenshots (`android.screenshot`) are captured exclusively on demand to verify discrete task outcomes. Screen video or continuous frame streaming is prohibited.
2. **No Background Account Crawling**: When instructed to summarize messages or feeds, the agent only reads visible nodes rendered on the active window. It never silently traverses background account databases or crawls contacts.
3. **No Unrequested Notification Scraping**: Incoming notifications are not uploaded in real time. They are queried only when the user explicitly says *"Shivani, phone notifications summarize karo"*.
4. **Clipboard Privacy**: Reading or writing clipboard content never stores raw clipboard data into persistent audit logs (`audit.jsonl`).
5. **On-Device Activity Transparency**: All actions executed by SHIVANI are recorded in the mobile app's local `ActivityScreen` so the user can inspect what occurred at any time.

---

## 2. Cryptographic Storage & Key Management

- Device pairing tokens are stored in Android `EncryptedSharedPreferences` backed by the hardware **Android KeyStore** (AES-256 GCM).
- The laptop core stores paired device identities in a secure local vault.
- No static passwords or default credentials exist anywhere in the source repository.

---

## 3. Permission Engine Mapping

| Operation | Risk Level | Description |
|-----------|------------|-------------|
| `android.get_device_status` | `SAFE` | Non-destructive status and battery check |
| `android.launch_app` | `SAFE` | Opens user-instructed application with verification |
| `android.press_home` / `back` | `SAFE` | Standard system navigation |
| `android.list_photos` | `SAFE` | Queries photo metadata matching query filter |
| `android.transfer_file` | `SAFE` | Transfers selected photo to temporary workflow cache |
| `android.pair_device` | `SENSITIVE` | Authenticates and registers new hardware |
| `android.read_clipboard` | `SENSITIVE` | Inspects clipboard data |
| `android.write_clipboard` | `SENSITIVE` | Writes text to clipboard |
| `android.prepare_social_action` | `SAFE` | Prepares draft preview without publishing |
| `android.execute_social_action` | `CRITICAL` | Publishes post, comment, or message (Requires confirmation) |

---

## 4. Human-in-the-Loop Safety Gate

Social media actions enforce the five-stage discipline:
```
1. PREPARE        (Assemble target node, action type, and payload)
2. SHOW TARGET    (Display post snippet or profile in approval card)
3. SHOW ACTION    (Present comment or post text clearly to user)
4. REQUEST APPROVAL (Wait for explicit user confirmation)
5. EXECUTE & VERIFY (Dispatch tap/type and confirm publication status)
```
