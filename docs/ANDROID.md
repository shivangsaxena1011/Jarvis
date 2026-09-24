# SHIVANI — Android Phone Agent Architecture

The Android Phone Agent enables SHIVANI to control and query the user's paired Android smartphone through natural language instructions in English, Hindi, and Hinglish.

---

## 1. High-Level Architecture

```
User Voice / Task Input
        │
        ▼
   Orchestrator
        │
        ▼
   Phone Agent ──(AppResolver, UIObserver, PhoneContext)
        │
        ▼
   Device Bridge ──(Mutual Authentication, HMAC Tokens, Heartbeat)
        │
   [TLS / Encrypted WebSockets]
        │
        ▼
   Android Phone (SHIVANI MOBILE)
   ├── ShivaniDeviceService (Foreground Keepalive)
   ├── ShivaniAccessibilityService (UI Nodes & Gestures)
   ├── UIAutomationManager (Launch & Gestures)
   ├── KeyStoreManager (Encrypted Credentials)
   └── ActivityLogger (On-Device Audit Trail)
```

---

## 2. Natural Language App Discovery (`AppResolver`)

The agent understands conversational Indian phrasing and maps it to installed Android package names:
- *"Shivani, phone mein Instagram kholo."* ──▶ `com.instagram.android`
- *"Shivani, phone ki settings kholo."* ──▶ `com.android.settings`
- *"Shivani, meri photos kholo."* ──▶ `com.google.android.apps.photos`
- *"Shivani, phone pe Chrome kholo."* ──▶ `com.android.chrome`
- *"Shivani, phone pe YouTube chalao."* ──▶ `com.google.android.youtube`
- *"Shivani, phone mein LinkedIn kholo."* ──▶ `com.linkedin.android`
- *"Shivani, WhatsApp open karo."* ──▶ `com.whatsapp`

### Verification Discipline
The agent never assumes an app launched successfully. After sending the launch command over the bridge, it queries the phone's active package and window state to confirm the application is running in the foreground before reporting *"Instagram is open on phone"*.

---

## 3. Minimalist Accessibility UI Observation (`AndroidUIObserver`)

Rather than streaming continuous screenshots or transmitting entire view hierarchies, the agent uses **Data Minimization**:
1. Traverses the accessibility node tree from `rootInActiveWindow`.
2. Filters out decorative layouts, containers, and non-interactive nodes.
3. Transmits only actionable nodes (buttons, text fields, lists, message items) with text, content descriptions, and bounds.
4. Matches user targets by semantic text, content description, or ID.
5. Dispatches gestures via `AccessibilityService.dispatchGesture`.

---

## 4. Social Media Safety Gates

For sensitive social actions (e.g. posting, commenting, following, liking):
```
PREPARE ──▶ SHOW TARGET ──▶ SHOW ACTION ──▶ REQUEST APPROVAL ──▶ EXECUTE ──▶ VERIFY
```
Example:
```
Action Staged:
Target: Post by Priya Sharma: 'Outstanding AI engineering architecture!'
Action: Comment
Content: 'Thank you Priya! Built with full verification discipline.'

Requires explicit human approval before execution.
```

---

## 5. Photo & Cross-Device Workflows

- `android.list_photos`: Search device photos by keywords, tags, or dates.
- `android.transfer_file`: Securely transfers the chosen photo to the laptop workspace for use in cross-application workflows (e.g. Recipe 6: Phone photo ──▶ LinkedIn draft preview ──▶ Approval gate ──▶ Publish).
- Temporary files are stored in `workspace/shivani-artifacts/temp_transfers/`.
