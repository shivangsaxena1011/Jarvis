# Multi-Monitor Layout & High-DPI Normalization — Phase 17

## 1. Monitor Layout Model
`MonitorLayout` represents physical and logical display configurations:
- `monitor_id`: Display index.
- `name`: Display device string.
- `is_primary`: Primary monitor flag.
- `width` / `height`: Resolution in logical pixels.
- `scale_factor`: OS DPI scaling ratio (e.g. 1.0 for 100%, 1.25 for 125%, 1.5 for 150%).
- `left` / `top`: Display offset on the virtual desktop.

---

## 2. DPI Coordinate Normalization
Screenshots are captured in physical pixel dimensions, whereas Win32 input calls (`SetCursorPos`, `mouse_event`) operate in logical desktop coordinates.

`CoordinateTransformer` scales bounding boxes:
$$\text{Logical Coordinate} = \frac{\text{Physical Pixel}}{\text{Scale Factor}}$$

This ensures clicks land accurately on target controls regardless of whether the user is on a 1080p display at 100% or a 4K display at 175% scaling.
