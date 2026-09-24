"""
SHIVANI Screen Diffing and Visual State Delta Engine.
"""

from typing import Union, Optional
import numpy as np
from PIL import Image

from vision.models.types import BoundingBox, CoordinateSpace
from vision.models.schemas import VisualDelta


def compute_screen_delta(
    img_before: Union[str, Image.Image],
    img_after: Union[str, Image.Image],
    threshold: int = 20,
) -> VisualDelta:
    """
    Computes visual delta between before and after screenshots using numpy array difference.
    """
    im1 = Image.open(img_before) if isinstance(img_before, str) else img_before
    im2 = Image.open(img_after) if isinstance(img_after, str) else img_after

    if im1.size != im2.size:
        # Resize im2 to match im1 if dimensions differ slightly
        im2 = im2.resize(im1.size, Image.Resampling.BILINEAR)

    arr1 = np.array(im1.convert("RGB"), dtype=np.int32)
    arr2 = np.array(im2.convert("RGB"), dtype=np.int32)

    diff = np.abs(arr1 - arr2)
    # Changed pixels where any RGB channel exceeds threshold
    changed_mask = np.any(diff > threshold, axis=2)

    total_pixels = changed_mask.size
    changed_count = int(np.count_nonzero(changed_mask))
    change_pct = (changed_count / total_pixels) * 100.0

    if changed_count < 100 or change_pct < 0.01:
        return VisualDelta(
            has_changed=False,
            change_percentage=change_pct,
            changed_region=None,
            description="No significant visual changes detected.",
        )

    # Find bounding box enclosing the changed pixels
    ys, xs = np.where(changed_mask)
    min_x, max_x = int(np.min(xs)), int(np.max(xs))
    min_y, max_y = int(np.min(ys)), int(np.max(ys))

    changed_box = BoundingBox(
        x=float(min_x),
        y=float(min_y),
        width=float(max_x - min_x + 1),
        height=float(max_y - min_y + 1),
        coordinate_space=CoordinateSpace.PHYSICAL,
    )

    desc = f"Screen updated in {int(changed_box.width)}x{int(changed_box.height)} region ({change_pct:.2f}% screen delta)."

    return VisualDelta(
        has_changed=True,
        change_percentage=round(change_pct, 3),
        changed_region=changed_box,
        description=desc,
    )
