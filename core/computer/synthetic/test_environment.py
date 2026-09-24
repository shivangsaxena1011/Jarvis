"""
SHIVANI Synthetic GUI Test Environment (Phase 17).
Generates deterministic synthetic desktop observations, forms, dialogs,
adversarial scenarios, and mock transitions for automated testing.
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional
from core.computer.models import (
    ApplicationContext,
    ApplicationState,
    DesktopObservation,
    ElementSource,
    ElementType,
    MonitorLayout,
    RectBounds,
    UIElement,
)


class SyntheticGUIEnvironment:
    """Simulates realistic GUI screens, dialogs, and state transitions."""

    def __init__(self):
        self.active_screen_type = "form"
        self.state_counter = 0

    def generate_form_screen(self, form_title: str = "Project Settings") -> DesktopObservation:
        """Generates a standard form with text boxes, checkboxes, and buttons."""
        elements = [
            UIElement(
                id="win_main",
                type=ElementType.WINDOW,
                text=form_title,
                bounds=RectBounds(left=100, top=100, width=800, height=600),
            ),
            UIElement(
                id="lbl_name",
                type=ElementType.CARD,
                text="Project Name:",
                bounds=RectBounds(left=120, top=150, width=120, height=25),
                parent_id="win_main",
            ),
            UIElement(
                id="txt_name",
                type=ElementType.TEXT_FIELD,
                text="",
                value="Default Project",
                bounds=RectBounds(left=250, top=150, width=300, height=25),
                parent_id="win_main",
                focused=True,
            ),
            UIElement(
                id="chk_enable",
                type=ElementType.CHECKBOX,
                text="Enable Telemetry",
                bounds=RectBounds(left=120, top=200, width=180, height=25),
                parent_id="win_main",
                selected=False,
            ),
            UIElement(
                id="btn_cancel",
                type=ElementType.BUTTON,
                text="Cancel",
                bounds=RectBounds(left=380, top=500, width=80, height=35),
                parent_id="win_main",
            ),
            UIElement(
                id="btn_save",
                type=ElementType.BUTTON,
                text="Save",
                bounds=RectBounds(left=480, top=500, width=80, height=35),
                parent_id="win_main",
            ),
        ]

        return DesktopObservation(
            active_window=form_title,
            elements=elements,
            monitors=[MonitorLayout()],
            application_context=ApplicationContext(
                app_name="SyntheticApp",
                window_title=form_title,
                state=ApplicationState.READY,
            ),
        )

    def generate_modal_dialog_screen(
        self,
        dialog_title: str = "Save Changes?",
        dialog_type: str = "CONFIRMATION",
    ) -> DesktopObservation:
        """Generates a modal dialog with Save, Don't Save, and Cancel options."""
        elements = [
            UIElement(
                id="dlg_root",
                type=ElementType.DIALOG,
                text=dialog_title,
                bounds=RectBounds(left=300, top=250, width=400, height=200),
            ),
            UIElement(
                id="dlg_msg",
                type=ElementType.CARD,
                text="Do you want to save changes to Document1?",
                bounds=RectBounds(left=320, top=290, width=360, height=40),
                parent_id="dlg_root",
            ),
            UIElement(
                id="btn_dont_save",
                type=ElementType.BUTTON,
                text="Don't Save",
                bounds=RectBounds(left=350, top=380, width=90, height=30),
                parent_id="dlg_root",
            ),
            UIElement(
                id="btn_dlg_cancel",
                type=ElementType.BUTTON,
                text="Cancel",
                bounds=RectBounds(left=460, top=380, width=80, height=30),
                parent_id="dlg_root",
            ),
            UIElement(
                id="btn_dlg_save",
                type=ElementType.BUTTON,
                text="Save",
                bounds=RectBounds(left=560, top=380, width=80, height=30),
                parent_id="dlg_root",
            ),
        ]

        return DesktopObservation(
            active_window=dialog_title,
            elements=elements,
            monitors=[MonitorLayout()],
            application_context=ApplicationContext(
                app_name="DocumentEditor",
                window_title=dialog_title,
                state=ApplicationState.DIALOG_OPEN,
            ),
        )

    def generate_auth_challenge_screen(self) -> DesktopObservation:
        """Generates an authentication / CAPTCHA security challenge."""
        elements = [
            UIElement(
                id="dlg_auth",
                type=ElementType.DIALOG,
                text="Authentication Required",
                bounds=RectBounds(left=350, top=200, width=450, height=300),
            ),
            UIElement(
                id="lbl_captcha",
                type=ElementType.CARD,
                text="Security Check: Please solve the CAPTCHA or enter your PIN to continue.",
                bounds=RectBounds(left=370, top=240, width=410, height=60),
                parent_id="dlg_auth",
            ),
        ]
        return DesktopObservation(
            active_window="Authentication Required",
            elements=elements,
            monitors=[MonitorLayout()],
            application_context=ApplicationContext(
                app_name="SecurityAgent",
                window_title="Authentication Required",
                state=ApplicationState.DIALOG_OPEN,
            ),
        )

    def generate_adversarial_duplicate_labels_screen(self) -> DesktopObservation:
        """Generates screen with misleading duplicate button labels."""
        elements = [
            UIElement(
                id="btn_cancel_1",
                type=ElementType.BUTTON,
                text="Cancel",
                bounds=RectBounds(left=100, top=200, width=80, height=30),
                source=ElementSource.OCR,
                confidence=0.60,
            ),
            UIElement(
                id="btn_cancel_2",
                type=ElementType.BUTTON,
                text="Cancel",
                bounds=RectBounds(left=400, top=200, width=80, height=30),
                source=ElementSource.ACCESSIBILITY,
                confidence=0.62,
            ),
        ]
        return DesktopObservation(
            active_window="Adversarial Ambiguity Test",
            elements=elements,
            monitors=[MonitorLayout()],
        )

    def generate_table_screen(self) -> DesktopObservation:
        """Generates a data table screen with columns and rows."""
        elements = [
            UIElement(
                id="tbl_data",
                type=ElementType.TABLE,
                text="Sales Data 2026",
                bounds=RectBounds(left=100, top=100, width=600, height=400),
            ),
            UIElement(
                id="col_month",
                type=ElementType.COLUMN,
                text="Month",
                bounds=RectBounds(left=100, top=100, width=200, height=30),
                parent_id="tbl_data",
            ),
            UIElement(
                id="col_sales",
                type=ElementType.COLUMN,
                text="Revenue",
                bounds=RectBounds(left=300, top=100, width=200, height=30),
                parent_id="tbl_data",
            ),
            UIElement(
                id="row_1",
                type=ElementType.ROW,
                text="January: $45,000",
                bounds=RectBounds(left=100, top=135, width=400, height=30),
                parent_id="tbl_data",
            ),
            UIElement(
                id="row_2",
                type=ElementType.ROW,
                text="February: $52,000",
                bounds=RectBounds(left=100, top=170, width=400, height=30),
                parent_id="tbl_data",
            ),
        ]
        return DesktopObservation(
            active_window="Spreadsheet Viewer",
            elements=elements,
            monitors=[MonitorLayout()],
            application_context=ApplicationContext(
                app_name="ExcelViewer",
                window_title="Spreadsheet Viewer",
                state=ApplicationState.READY,
            ),
        )
