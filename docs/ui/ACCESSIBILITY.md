# SHIVANI Accessibility & Assistive Tech Standards

## 1. Compliance Baseline
SHIVANI Desktop meets **WCAG 2.1 AA** accessibility standards to ensure an inclusive experience across all user capabilities.

---

## 2. Keyboard Navigation & Global Shortcuts

Every action in SHIVANI can be initiated and controlled purely through the keyboard:

| Shortcut | Context | Action |
| :--- | :--- | :--- |
| `Ctrl + Space` | Global Desktop | Open / Dismiss Spotlight Command Bar. |
| `Ctrl + Win + Space` | Global Desktop | Push-to-Talk (Hold to Speak). |
| `Ctrl + Shift + S` | Global Desktop | Immediate Emergency Stop (All Tasks). |
| `Ctrl + L` | In-App | Lock Assistant Screen. |
| `Ctrl + P` | In-App | Toggle Privacy Mode (Mic + Screen Blinder). |
| `Escape` | In-App | Dismiss Modals, Popovers, and Command Bar. |
| `Tab` / `Shift + Tab`| In-App | Sequential navigation across interactive controls. |
| `Enter` | In-App | Submit command, confirm selected approval. |

---

## 3. Assistive Display Features

1. **High Contrast Mode**:
   - Distinctive border highlights and minimum `7:1` contrast ratio for essential status indicators.
2. **ARIA Live Regions**:
   - `aria-live="polite"` applied to conversational chat output and assistant status badge so screen readers announce state transitions and replies.
3. **Motion Sensitivity (`prefers-reduced-motion`)**:
   - Disables all pulsing orb glows, continuous spinning orbit rings, and animated page transitions.
4. **Focus Rings**:
   - Unambiguous `2px solid var(--accent-cyan)` outline on every focused button, input field, and navigation tab.
