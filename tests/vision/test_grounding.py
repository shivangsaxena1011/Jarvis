"""
Tests for Target Grounding Engine.
"""

from vision.models.types import BoundingBox, VisualElementType, MonitorInfo
from vision.models.schemas import UIElement, VisualContext
from vision.grounding.grounding_engine import GroundingEngine


def test_direct_target_grounding():
    engine = GroundingEngine()

    elements = [
        UIElement(
            id="btn_submit",
            element_type=VisualElementType.BUTTON,
            bounding_box=BoundingBox(x=300, y=400, width=120, height=40),
            text="Submit Form",
        ),
        UIElement(
            id="btn_cancel",
            element_type=VisualElementType.BUTTON,
            bounding_box=BoundingBox(x=450, y=400, width=100, height=40),
            text="Cancel",
        ),
        UIElement(
            id="inp_email",
            element_type=VisualElementType.INPUT,
            bounding_box=BoundingBox(x=300, y=250, width=300, height=40),
            text="Email Address",
        ),
    ]

    ctx = VisualContext(
        screenshot_path="/tmp/test.png",
        timestamp=1000.0,
        monitor=MonitorInfo(id=0),
        elements=elements,
    )

    elem, point, conf = engine.ground("Submit", ctx)
    assert elem is not None
    assert elem.id == "btn_submit"
    assert point.x == 360.0
    assert point.y == 420.0
    assert conf > 0.50

    elem_cancel, pt_cancel, conf_cancel = engine.ground("Cancel button", ctx)
    assert elem_cancel is not None
    assert elem_cancel.id == "btn_cancel"


def test_spatial_relative_grounding():
    engine = GroundingEngine()

    label_user = UIElement(
        id="lbl_user",
        element_type=VisualElementType.TEXT,
        bounding_box=BoundingBox(x=200, y=100, width=100, height=30),
        text="Username",
    )
    inp_user = UIElement(
        id="inp_user",
        element_type=VisualElementType.INPUT,
        bounding_box=BoundingBox(x=200, y=150, width=250, height=40),
        text="",
    )
    label_pass = UIElement(
        id="lbl_pass",
        element_type=VisualElementType.TEXT,
        bounding_box=BoundingBox(x=200, y=220, width=100, height=30),
        text="Password",
    )
    inp_pass = UIElement(
        id="inp_pass",
        element_type=VisualElementType.INPUT,
        bounding_box=BoundingBox(x=200, y=270, width=250, height=40),
        text="",
    )

    ctx = VisualContext(
        screenshot_path="/tmp/test.png",
        timestamp=1000.0,
        monitor=MonitorInfo(id=0),
        elements=[label_user, inp_user, label_pass, inp_pass],
    )

    # Query: "input below Username"
    elem, point, conf = engine.ground("input below Username", ctx)
    assert elem is not None
    assert elem.id == "inp_user"
    assert conf > 0.50

    # Query: "input below Password"
    elem_p, _, _ = engine.ground("input below Password", ctx)
    assert elem_p is not None
    assert elem_p.id == "inp_pass"
