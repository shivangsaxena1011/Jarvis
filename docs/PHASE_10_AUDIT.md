# SHIVANI — Comprehensive Phase 10 Vision & GUI Intelligence Audit

**Date**: September 24, 2026  
**Auditor**: Senior Computer Vision & Autonomous Systems Architect  
**Scope**: Computer Vision, Screen Understanding, OCR, Multi-Monitor High-DPI GUI Interaction, and Spatial Grounding  
**Baseline**: Phase 9 Verified (`8d94ad4`, 162/162 Passing Tests, 151 Registered Tools)

---

## 1. Executive Summary

Phase 10 transforms SHIVANI from an accessibility-driven and coordinate-blind automation agent into a **fully sighted, spatially reasoning, multi-modal GUI operating intelligence**. 

While Phases 1–9 established robust OS execution, multi-agent workflows, browser orchestration, and memory persistence, GUI interaction previously relied almost exclusively on:
1. Native Windows UI Automation (pywinauto / accessibility trees).
2. Browser DOM trees (Playwright).
3. Android accessibility dumps.
4. Hardcoded pixel coordinates or rudimentary full-screen screenshots without DPI conversion.

This audit establishes the blueprint for **Phase 10: Advanced Visual Computer Intelligence**, incorporating multi-monitor high-DPI screen capture, pluggable multilingual OCR, visual UI element detection, spatial layout reasoning, multi-source fusion (Accessibility + DOM + Vision), visual verification diffing, and privacy-first redaction.

---

## 2. Existing Visual & GUI Observation State Assessment

### 2.1 Existing Screen Capture (`tools/desktop/screen.py` & `tools/desktop/screen_tools.py`)
- **Status**: Basic `ScreenCapture` class wrapping `pyautogui.screenshot()` or PIL fallback.
- **Deficiencies**:
  - Unaware of Windows High-DPI scaling (e.g., 125%, 150%, 200%). On 4K or modern laptop displays, physical pixel coordinates captured do not match logical Win32 mouse click coordinates, causing missed clicks.
  - Multi-monitor unawareness: Captures primary monitor only or naively treats multiple monitors as a single uncalibrated canvas.
  - No active window clipping or window handle-based (`hwnd`) capture without desktop occlusion.
  - Performance: Uses slow Pillow/pyautogui image grabs rather than accelerated multi-monitor capture (e.g., `mss` or Win32 BitBlt).

### 2.2 Existing Computer Observation (`agents/computer/observation.py`)
- **Status**: Implements `DesktopObserver` combining active window titles, process names, and pywinauto accessibility controls.
- **Deficiencies**:
  - Completely blind to custom-rendered UI frameworks: Canvas apps, Electron apps without accessibility flags, Flutter, Qt, game windows, and remote desktop streams.
  - Elements lacking accessibility descriptors are completely invisible to the agent.

### 2.3 Existing Vision Stub (`agents/computer/vision.py`)
- **Status**: Contains abstract `VisionProvider` and `MockVisionProvider` with 3 static hardcoded elements (`Search box`, `Submit button`, `Close window`).
- **Deficiencies**:
  - No real vision model integration.
  - No OCR integration (words, lines, blocks, bounding boxes).
  - No spatial relationship queries (e.g., "click the icon to the right of 'Profile'").
  - No verification of state change (before-and-after screenshot diffing).

### 2.4 Browser & Mobile Observers (`agents/browser/observer.py`, `agents/phone/ui_observer.py`)
- **Status**: Both extract structured hierarchies (DOM nodes and Android node dumps).
- **Synergy Opportunity**: Vision should not replace DOM or Android accessibility; rather, it must **fuse** with them to validate element visibility, rendered bounding boxes, and handle non-standard custom canvas controls.

---

## 3. Core Architecture of Phase 10 Vision Intelligence

```
                        Physical Screen(s) / Multi-Monitor
                                       │
                                       ▼
                     High-DPI Screen Capture (`vision/capture`)
                     (Physical ↔ Logical ↔ Normalized Coords)
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
     OCR Subsystem (`vision/ocr`)                    UI Element Detector (`vision/ui`)
   (Tesseract / WinMedia / VLM / Mock)             (Buttons, Inputs, Modals, Tables, Icons)
   (Bounding boxes, Text, Hinglish)                (Edge, Contour, Visual Classifier)
            │                                                     │
            └──────────────────────────┬──────────────────────────┘
                                       ▼
                       Visual UI Tree (`vision/ui/ui_tree`)
                        (Hierarchical Spatial Containers)
                                       │
                                       ▼
                  Multi-Source Fusion (`vision/models/schemas`)
                   (Accessibility + DOM + OCR + Visual Nodes)
                                       │
                                       ▼
                 Spatial Reasoning & Grounding (`vision/reasoning`)
                 (Directions, Proximity, Relative Target Grounding)
                                       │
                                       ▼
                   Privacy & Masking (`vision/privacy/redaction`)
                    (Passwords, OTPs, CC, Sensitive Regions)
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
 Vision Model / VLM (`vision/providers`)        Action & Verification (`vision/verification`)
(Screen Q&A, Natural Scene Description)         (Pre/Post Diffing, Visual State Change)
```

---

## 4. Key Subsystems & Design Specifications

### 4.1 Coordinate Space Transformations (`vision/capture/coordinates.py`)
Three distinct coordinate spaces must be maintained with mathematical conversions:
1. **Physical Coordinates** ($X_p, Y_p$): Exact hardware pixels of the screenshot bitmap (e.g., 3840×2160 on a 4K display).
2. **Logical UI Coordinates** ($X_l, Y_l$): System desktop coordinates used by OS input injectors (`pyautogui.click`, `SendInput`) scaled by DPI factor (e.g., 150% scaling = 2560×1440).
3. **Normalized Coordinates** ($u, v \in [0.0, 1.0]$): Resolution-independent floating point coordinates for multi-device vision reasoning and LLM prompts.

Formula:
$$X_l = \frac{X_p}{\text{ScaleFactor}}, \quad Y_l = \frac{Y_p}{\text{ScaleFactor}}$$
$$u = \frac{X_p}{\text{Width}_p}, \quad v = \frac{Y_p}{\text{Height}_p}$$

### 4.2 Multi-Monitor Awareness (`vision/capture/monitors.py`)
- Enumerate all active displays with `MonitorInfo(id, x, y, width, height, scale_factor, is_primary)`.
- Support capturing all monitors, primary monitor, or a target secondary monitor by ID or window placement.

### 4.3 Pluggable Multilingual OCR (`vision/ocr/`)
- Unified `OCRResult` containing hierarchical `OCRBlock` $\rightarrow$ `OCRLine` $\rightarrow$ `OCRWord` with exact bounding boxes, confidence scores $[0.0, 1.0]$, and script tags.
- Support fuzzy text lookup (`find_text("Settings", fuzzy=True, threshold=0.8)`).
- Backends:
  - `TesseractOCRBackend` (local, high performance).
  - `WindowsOCRBackend` / `VisionModelOCRBackend`.
  - `MockOCRBackend` (deterministic testing with synthetic layouts).
- Language support: English, Hindi (Devanagari), Hinglish phonetics.

### 4.4 Visual UI Element Detection (`vision/ui/`)
- Detect visual elements: `button`, `input_field`, `checkbox`, `radio`, `dropdown`, `card`, `dialog_modal`, `table`, `icon`, `tab`.
- Compute visual attributes: background color contrast, borders, state (`focused`, `disabled`, `checked`, `hovered`).
- Build hierarchical `VisualUITree` using containment geometry (e.g., button inside a toolbar inside a modal window).

### 4.5 Spatial Reasoning & Grounding (`vision/grounding/`, `vision/reasoning/`)
- Natural language spatial queries:
  - `"button to the right of 'Cancel'"`
  - `"input field below 'Password'"`
  - `"first item inside sidebar"`
  - `"red button at top-right corner"`
- Confidence-scored resolution: Combines text match score + spatial relation match score + visual element type confidence.

### 4.6 Verification & Screen Diffing (`vision/verification/`)
- `VisualVerifier` compares screen state before action ($S_0$) and after action ($S_1$).
- Calculates:
  - Region changed (bounding box of visual delta).
  - Percentage of screen changed.
  - New elements appeared (e.g., modal dialog opened, loading spinner vanished, error message displayed).
  - Validates success/failure of click, type, or submit actions.

### 4.7 Privacy Redaction & Security (`vision/privacy/`)
- Automatic detection of sensitive UI regions:
  - Password inputs (marked by OS accessibility or detected by visual masked characters `••••••`).
  - Credit card number patterns, CVV, OTP codes, API keys in OCR text.
  - User-configured exclusion zones.
- Solid color or blur masking before saving to disk or sending to cloud vision models.

---

## 5. Implementation Roadmap & Verification Strategy

1. **Step 1: Core Vision Foundation & Models**:
   - `vision/models/types.py`, `vision/models/schemas.py`.
2. **Step 2: Capture, Monitor & High-DPI Engine**:
   - `vision/capture/screen_capture.py`, `vision/capture/coordinates.py`, `vision/capture/monitors.py`.
3. **Step 3: OCR Subsystem**:
   - `vision/ocr/engine.py`, `vision/ocr/fuzzy.py`, `vision/ocr/multilingual.py`.
4. **Step 4: UI Detection & Layout**:
   - `vision/ui/element_detector.py`, `vision/ui/ui_tree.py`, `vision/layout/layout_analyzer.py`.
5. **Step 5: Spatial Reasoning & Target Grounding**:
   - `vision/reasoning/spatial.py`, `vision/grounding/target_grounder.py`.
6. **Step 6: Screen Diffing, Error Detection & Verification**:
   - `vision/verification/screen_diff.py`, `vision/verification/visual_verifier.py`.
7. **Step 7: Privacy & Redaction**:
   - `vision/privacy/redactor.py`.
8. **Step 8: Vision Model Provider Interface**:
   - `vision/providers/vlm.py`.
9. **Step 9: Agent Integration**:
   - Connect vision engine into `ComputerAgent`, `BrowserAgent`, `PhoneAgent`.
10. **Step 10: Exhaustive Test Suite**:
    - Build test suite under `tests/vision/` covering every component with 100% deterministic reproducibility.
    - Full regression test run across existing 162 tests.
