# Desktop Observation Model — Phase 17

## 1. Overview
The `DesktopObservation` model represents the agent's complete, unified model of the computer's world state at any given instant.

Unlike naive screen-scraping bots that only hold an image buffer, Shivani's observation fuses:
1. **Window Hierarchy**: Active window, process ID, title, and all open visible OS windows.
2. **Display Topography**: Multi-monitor resolutions, DPI scaling, and physical coordinate bounds.
3. **Accessibility Tree**: Control types, native accessibility names, values, and states via Windows UI Automation (`pywinauto` / `UIAutomationCore`).
4. **Visual Elements**: Bounding boxes, layout groups, and visual containers detected by CV models.
5. **Textual Content**: OCR text snippets with confidence values and spatial coordinates.
6. **Interaction Peripherals**: Cursor position and active clipboard text with automatic privacy redaction.
7. **Application Context**: Identified application name, process metadata, and known project workspace paths.

---

## 2. Structured UI Element Schema

Every detected control on screen conforms to the typed `UIElement` schema:

```python
class UIElement(BaseModel):
    id: str                        # Unique UUID
    type: ElementType              # BUTTON, TEXT_FIELD, CHECKBOX, RADIO, TAB, MENU, etc.
    text: str                      # Visible label or accessible name
    role: str                      # OS role (e.g., 'Button', 'MenuItem', 'Edit')
    bounds: RectBounds             # (left, top, width, height) in logical coordinates
    enabled: bool                  # Interactive state
    visible: bool                  # Visibility state
    focused: bool                  # Keyboard focus state
    selected: bool                 # Selection state (for radio/checkbox/tabs)
    value: Optional[str]           # Input field text or slider value
    confidence: float              # Grounding confidence (0.0 to 1.0)
    source: ElementSource          # ACCESSIBILITY, DOM, APPLICATION_API, OCR, VISION, SPATIAL
    parent_id: Optional[str]       # Container ID in semantic tree
    children_ids: List[str]        # Child element IDs
```

---

## 3. Privacy Safeguards
When capturing desktop observations:
- System clipboard contents are scanned for sensitive tokens (passwords, JWTs, bearer tokens, API keys, private keys).
- Detected secrets are replaced with `[REDACTED_SENSITIVE_CLIPBOARD]` and flagged with `clipboard_is_sensitive = True`.
- Sensitive data is never saved to disk in plain text or persisted in audit logs.
