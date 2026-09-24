"""
Unit tests for Phase 17 Desktop Observation, Semantic Graph, Spatial Reasoning, and Visual Grounding.
"""

import pytest
from core.computer.models import (
    ElementSource,
    ElementType,
    MonitorLayout,
    RectBounds,
    UIElement,
)
from core.computer.observation_engine import ObservationEngine
from core.computer.semantic_graph import UISemanticGraph
from core.computer.spatial_engine import SpatialEngine
from core.computer.synthetic import SyntheticGUIEnvironment
from core.computer.visual_grounding import MultiSourceGrounder


def test_synthetic_form_observation():
    env = SyntheticGUIEnvironment()
    obs = env.generate_form_screen("Settings Dialog")

    assert obs.active_window == "Settings Dialog"
    assert len(obs.elements) == 6
    assert len(obs.monitors) == 1

    # Text search
    save_btns = obs.find_elements_by_text("Save", exact=True)
    assert len(save_btns) == 1
    assert save_btns[0].type == ElementType.BUTTON


def test_spatial_reasoning_predicates():
    spatial = SpatialEngine()

    # Create layout: Left Button, Middle Search, Right Submit
    btn_left = UIElement(id="b1", text="Back", bounds=RectBounds(left=100, top=100, width=50, height=30))
    search_box = UIElement(id="s1", text="Search", bounds=RectBounds(left=180, top=100, width=200, height=30))
    btn_right = UIElement(id="b2", text="Submit", bounds=RectBounds(left=400, top=100, width=80, height=30))

    # Test left_of and right_of
    assert spatial.is_left_of(btn_left.bounds, search_box.bounds) is True
    assert spatial.is_right_of(btn_right.bounds, search_box.bounds) is True

    # Test between
    assert spatial.is_between(search_box.bounds, btn_left.bounds, btn_right.bounds) is True

    # Test near
    assert spatial.is_near(btn_left.bounds, search_box.bounds, max_distance=180) is True
    assert spatial.is_far(btn_left.bounds, btn_right.bounds, min_distance=250) is True

    # Test vertical above/below
    header = UIElement(id="h1", text="Header", bounds=RectBounds(left=100, top=40, width=400, height=40))
    assert spatial.is_above(header.bounds, search_box.bounds) is True
    assert spatial.is_below(search_box.bounds, header.bounds) is True


def test_semantic_graph_navigation():
    # Window with Toolbar (containing Save) and Main Area
    win = UIElement(id="w1", type=ElementType.WINDOW, text="Editor", bounds=RectBounds(left=0, top=0, width=1000, height=800))
    toolbar = UIElement(id="tb1", type=ElementType.CARD, role="Toolbar", text="Main Toolbar", bounds=RectBounds(left=0, top=0, width=1000, height=50), parent_id="w1")
    btn_save = UIElement(id="b_save", type=ElementType.BUTTON, text="Save", bounds=RectBounds(left=10, top=10, width=60, height=30), parent_id="tb1")

    graph = UISemanticGraph([win, toolbar, btn_save])

    found = graph.find_in_section("Toolbar", "Save")
    assert found is not None
    assert found.id == "b_save"

    path = graph.get_path_to_element("b_save")
    assert "Editor" in path
    assert "Save" in path


def test_visual_grounding_multi_source():
    grounder = MultiSourceGrounder(confidence_threshold=0.60)

    elements = [
        UIElement(id="e1", type=ElementType.BUTTON, text="Cancel", bounds=RectBounds(left=200, top=300, width=70, height=30), source=ElementSource.ACCESSIBILITY),
        UIElement(id="e2", type=ElementType.BUTTON, text="Save", bounds=RectBounds(left=300, top=300, width=70, height=30), source=ElementSource.ACCESSIBILITY),
        UIElement(id="e3", type=ElementType.TEXT_FIELD, text="Username", bounds=RectBounds(left=100, top=100, width=150, height=30), source=ElementSource.DOM),
    ]

    # Ground exact button
    res_save = grounder.ground("Save button", elements)
    assert res_save.element is not None
    assert res_save.element.id == "e2"
    assert res_save.confidence >= 0.80
    assert res_save.ambiguous is False

    # Ground spatial relation
    res_spatial = grounder.ground("button to the right of Cancel", elements)
    assert res_spatial.element is not None
    assert res_spatial.element.id == "e2"

    # Ground ambiguous query
    res_ambig = grounder.ground("click that thing", elements)
    assert res_ambig.ambiguous is True
