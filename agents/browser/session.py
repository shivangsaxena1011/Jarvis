"""
SHIVANI Browser Session Management
Tracks session lifecycle, open tabs, active page, navigation history,
and contextual task state across browser operations.
"""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TabInfo(BaseModel):
    tab_id: str
    url: str = ""
    title: str = ""
    is_active: bool = False
    index: int = 0


class BrowserSession(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    browser_type: str = "chromium"
    profile_name: str = "default"
    active_tab_id: Optional[str] = None
    tabs: Dict[str, TabInfo] = Field(default_factory=dict)
    history: List[str] = Field(default_factory=list)
    last_action: Optional[str] = None
    last_query: Optional[str] = None
    task_id: Optional[str] = None

    def register_tab(self, tab_id: str, url: str = "", title: str = "", is_active: bool = True) -> TabInfo:
        idx = len(self.tabs)
        if is_active:
            for t in self.tabs.values():
                t.is_active = False
            self.active_tab_id = tab_id

        tab = TabInfo(tab_id=tab_id, url=url, title=title, is_active=is_active, index=idx)
        self.tabs[tab_id] = tab
        if url and (not self.history or self.history[-1] != url):
            self.history.append(url)
        return tab

    def update_tab(self, tab_id: str, url: Optional[str] = None, title: Optional[str] = None) -> None:
        if tab_id in self.tabs:
            if url:
                self.tabs[tab_id].url = url
                if not self.history or self.history[-1] != url:
                    self.history.append(url)
            if title:
                self.tabs[tab_id].title = title

    def switch_tab(self, identifier: Any) -> Optional[str]:
        """Switches active tab by tab_id or numerical index (0-based)."""
        target_id = None
        if isinstance(identifier, int):
            for tid, tab in self.tabs.items():
                if tab.index == identifier:
                    target_id = tid
                    break
        elif str(identifier) in self.tabs:
            target_id = str(identifier)

        if target_id:
            for t in self.tabs.values():
                t.is_active = (t.tab_id == target_id)
            self.active_tab_id = target_id
            return target_id
        return None

    def remove_tab(self, tab_id: str) -> None:
        self.tabs.pop(tab_id, None)
        if self.active_tab_id == tab_id:
            # Set another tab active if available
            if self.tabs:
                next_tab = next(iter(self.tabs.values()))
                next_tab.is_active = True
                self.active_tab_id = next_tab.tab_id
            else:
                self.active_tab_id = None

    def list_tabs(self) -> List[Dict[str, Any]]:
        return [{**t.model_dump(), "id": t.tab_id} for t in sorted(self.tabs.values(), key=lambda x: x.index)]

    def record_action(self, action: str, query: Optional[str] = None) -> None:
        self.last_action = action
        if query:
            self.last_query = query
