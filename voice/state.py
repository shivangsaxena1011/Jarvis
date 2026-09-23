"""
SHIVANI Audio State Machine
Manages voice lifecycle: IDLE -> LISTENING -> PROCESSING -> SPEAKING -> ERROR.
Publishes real-time state changes to the EventBus and Desktop UI.
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from core.events.bus import EventBus, EventType, get_event_bus


class AudioState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"


class AudioStateManager:
    def __init__(self, event_bus: Optional[EventBus] = None):
        self._current_state = AudioState.IDLE
        self._previous_state = AudioState.IDLE
        self.events = event_bus or get_event_bus()
        self._listeners: List[Callable[[AudioState, AudioState], None]] = []

    @property
    def current_state(self) -> AudioState:
        return self._current_state

    @property
    def is_speaking(self) -> bool:
        return self._current_state == AudioState.SPEAKING

    @property
    def is_listening(self) -> bool:
        return self._current_state == AudioState.LISTENING

    def add_listener(self, callback: Callable[[AudioState, AudioState], None]) -> None:
        self._listeners.append(callback)

    def transition_to(self, new_state: AudioState, details: Optional[Dict[str, Any]] = None) -> AudioState:
        if new_state == self._current_state:
            return self._current_state

        old_state = self._current_state
        self._previous_state = old_state
        self._current_state = new_state

        event_data = {
            "old_state": old_state.value,
            "new_state": new_state.value,
            "details": details or {}
        }
        self.events.publish(EventType.SYSTEM_STATUS, data={"audio_state": event_data})

        for listener in self._listeners:
            try:
                listener(old_state, new_state)
            except Exception as e:
                print(f"[AUDIO STATE LISTENER ERROR] {e}")

        return self._current_state


# Global singleton
_global_audio_state = AudioStateManager()

def get_audio_state_manager() -> AudioStateManager:
    return _global_audio_state
