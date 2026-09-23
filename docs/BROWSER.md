# Browser Agent Architecture — SHIVANI

The Browser Agent enables automated web navigation, content extraction, and media control.

---

## 1. Engine & Driver
- **Primary Framework**: Playwright with async Python runtime.
- **Browser Profiles**: Chromium, Chrome, and Brave.
- **Session Persistence**: Reuses existing authenticated user sessions (cookies, stored storage states) to avoid repeating login flows.

---

## 2. Interaction Hierarchy
When operating elements on web pages:
1. **Accessibility Tree / ARIA Roles**: (`page.get_by_role("button", name="Search")`)
2. **Semantic Text Selectors**: (`page.get_by_text("Sign In")`)
3. **CSS / XPath Selectors**: Fallback for stable DOM targets.
4. **Visual & Coordinate Fallback**: Vision analysis when custom canvas or non-standard shadow roots are encountered.

---

## 3. Compliance & Security Boundaries
- Never bypasses CAPTCHAs, bot detections, or Cloudflare protection mechanisms.
- Operates strictly within user-granted session permissions.
- Destructive browser operations (e.g. purchasing items, deleting account records) strictly require explicit confirmation.
