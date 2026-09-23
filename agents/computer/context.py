"""
SHIVANI Current UI Context
Maintains active desktop state, foreground window, last screenshot,
active URL, selected file, and last interacted UI element.
Powers deictic references ("isko close karo", "yahan click karo").
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CurrentUIContext(BaseModel):
    active_application: Optional[str] = Field(default=None, description="Currently active application executable or name")
    active_window: Optional[str] = Field(default=None, description="Title of currently active window")
    active_pid: Optional[int] = Field(default=None, description="Process ID of currently active window")
    last_screenshot: Optional[str] = Field(default=None, description="Path to most recently captured screenshot")
    current_url: Optional[str] = Field(default=None, description="Current browser URL if browser is active")
    selected_file: Optional[str] = Field(default=None, description="Path of last selected or inspected file")
    last_interacted_element: Optional[str] = Field(default=None, description="Semantic description of last interacted UI element")
    current_task: Optional[str] = Field(default=None, description="ID of current executing task")
    history_windows: List[str] = Field(default_factory=list, description="Recent active window titles")

    def update_active_window(
        self,
        title: Optional[str] = None,
        app_name: Optional[str] = None,
        pid: Optional[int] = None
    ) -> None:
        """Updates active window and tracks in window history."""
        if title:
            self.active_window = title
            if not self.history_windows or self.history_windows[-1] != title:
                self.history_windows.append(title)
                if len(self.history_windows) > 20:
                    self.history_windows.pop(0)
        if app_name:
            self.active_application = app_name
        if pid:
            self.active_pid = pid

    def set_last_screenshot(self, path: str) -> None:
        self.last_screenshot = path

    def set_current_url(self, url: str) -> None:
        self.current_url = url

    def set_selected_file(self, file_path: str) -> None:
        self.selected_file = file_path

    def set_last_interacted_element(self, element: str) -> None:
        self.last_interacted_element = element

    def set_current_task(self, task_id: Optional[str]) -> None:
        self.current_task = task_id

    def get_deictic_target(self) -> Optional[str]:
        """Resolves referents like 'isko' or 'this' to the most salient current context."""
        return self.active_window or self.active_application or self.selected_file
