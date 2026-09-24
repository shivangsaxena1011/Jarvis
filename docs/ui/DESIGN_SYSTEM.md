# SHIVANI Design System & Styling Guide

## 1. Design Vision
SHIVANI's visual identity balances **modern elegance, technical depth, and calming clarity**. It is designed to feel like a high-performance personal AI operating system rather than a generic chat window.

---

## 2. Color System & Design Tokens

### 2.1 Dark Theme (`theme-dark`, Default)
- `--bg-primary`: `#0d1117` (Deep dark slate canvas)
- `--bg-secondary`: `#161b22` (Elevated card background)
- `--bg-tertiary`: `#21262d` (Hover states & borders)
- `--accent-cyan`: `#58a6ff` (Primary actions, active states)
- `--accent-purple`: `#bc8cff` (AI reasoning, planning, creative tasks)
- `--accent-emerald`: `#3fb950` (Completed tasks, safe actions, online status)
- `--accent-amber`: `#d29922` (Warnings, pending approvals, transcribing)
- `--accent-rose`: `#f85149` (Critical risk, errors, emergency stop)
- `--text-primary`: `#f0f6fc` (High contrast readability)
- `--text-secondary`: `#8b949e` (Metadata, timestamps, subheadings)
- `--text-muted`: `#484f58` (Placeholders, inactive tabs)

### 2.2 Light Theme (`theme-light`)
- Clean, high-contrast light workspace for bright environments:
- `--bg-primary`: `#f6f8fa`
- `--bg-secondary`: `#ffffff`
- `--bg-tertiary`: `#eaeef2`
- Text tokens dynamically invert for optimal contrast ratios (> 4.5:1).

### 2.3 Luminous Neon Theme (`theme-luminous`)
- High-saturation futuristic cyberpunk aesthetic for developer environments:
- Deep midnight canvas (`#050811`) with vibrant electric cyan (`#00f0ff`) and ultraviolet accents (`#a855f7`).

---

## 3. Typography Hierarchy

- **Font Family**: `-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif`
- **Monospace Family** (code blocks, paths, JSON, logs): `"Cascadia Code", "Fira Code", "JetBrains Mono", Consolas, monospace`
- **Scale**:
  - Display Title: `24px` / `700 bold`
  - Panel Header: `18px` / `600 semi-bold`
  - Body Text: `14px` / `400 regular` (line-height: `1.5`)
  - Secondary / Captions: `12px` / `400 regular`
  - Micro Badges & Tags: `11px` / `600 bold`

---

## 4. Assistant Orb Animations & Status Ring

The central HUD Orb provides an immediate, ambient visualization of the assistant's cognitive status:

| State | Orb Core Color | Glow Pulse | Animation Style |
| :--- | :--- | :--- | :--- |
| **IDLE** | Cyan / Slate | Gentle breath (4s cycle) | Subtle scale `1.0 -> 1.05` |
| **LISTENING** | Emerald Green | High-frequency pulse (1.2s) | Waveform audio reactivity |
| **PLANNING / REASONING**| Purple / Violet | Dual rotating orbit rings | Continuous spinning gradient |
| **EXECUTING / WORKING** | Vibrant Cyan | Fast pulse (0.8s) | Dynamic glowing aura |
| **WAITING APPROVAL** | Amber Yellow | Steady double blink | Urgent attention draw |
| **LOCKED / STOPPED** | Ruby Red | Static solid rim | No motion, locked icon |

---

## 5. Accessibility & Responsive Rules

1. **WCAG 2.1 AA Compliance**:
   - Contrast ratio for all text elements exceeds `4.5:1` against their respective card backgrounds.
   - Contrast ratio for large headers and buttons exceeds `3:1`.
2. **Keyboard Focus Outlines**:
   - Visible `2px solid var(--accent-cyan)` focus ring on all interactive elements during keyboard navigation.
3. **Reduced Motion Mode (`@media (prefers-reduced-motion)`)**:
   - Automatically disables pulsing orb animations, sliding transitions, and rotating spinners for users who prefer motion reduction.
