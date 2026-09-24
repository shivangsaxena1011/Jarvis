# Multi-Source UI Grounding & Spatial Reasoning — Phase 17

## 1. Grounding Hierarchy
Shivani never relies exclusively on raw screenshot pixels or fragile coordinates. Grounding uses a fused hierarchy of evidence:

```text
1. Accessibility / Windows UI Automation (UIA)
2. Browser DOM (Playwright)
3. Application Semantic APIs
4. Optical Character Recognition (OCR)
5. Visual Object Detection
6. Spatial Reasoning Predicates
7. Coordinate Fallback (Lowest confidence)
```

When multiple sources agree (e.g. UIA declares Button "Save" and OCR finds "Save" within the same bounding box), confidence is boosted to $>0.90$.

---

## 2. Spatial Predicates
Natural language instructions frequently describe controls by their relative position. `SpatialEngine` implements deterministic geometric calculations for:
- `above` / `below`: Vertical alignment checks with bounded horizontal overlap.
- `left_of` / `right_of`: Horizontal bounds checks with bounded vertical overlap.
- `inside` / `contains`: Complete geometric enclosure.
- `near` / `far`: Center-to-center Euclidean distance thresholds.
- `between`: Target position lying between reference elements A and B along horizontal or vertical axes.
- `aligned_with`: Center alignment within a configurable pixel tolerance.
- `adjacent_to`: Bounding boxes separated by less than a small gap threshold.

### Examples
- `"Click the button to the right of Search"`
- `"Click the checkbox below Username"`
- `"Click Cancel near the bottom right"`

---

## 3. Ambiguity & Confidence Gate
If a query matches multiple candidates with close scores, or if top confidence is below the threshold (`0.65`):
- The action is flagged with `ambiguous = True`.
- Shivani pauses and prompts the user for clarification rather than clicking blindly.
