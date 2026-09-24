"""
SHIVANI Focus Engine (Phase 16).
Manages dedicated focus sessions, suppresses distracting notifications,
and logs interruptions without intrusive psychological inferences.
"""

from datetime import datetime, timezone
import logging
from typing import Optional

from core.productivity.models import FocusSession
from core.productivity.store import ProductivityStore
from notifications.center import NotificationCenter

logger = logging.getLogger("shivani.productivity.focus_engine")


class FocusEngine:
    """Controls Focus Mode sessions and coordinates notification suppression."""

    def __init__(self, store: ProductivityStore, notification_center: Optional[NotificationCenter] = None):
        self.store = store
        self.notification_center = notification_center
        self._active_session: Optional[FocusSession] = None

    @property
    def active_session(self) -> Optional[FocusSession]:
        return self._active_session

    @property
    def is_focusing(self) -> bool:
        return self._active_session is not None

    def start_focus_session(
        self,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_title: str = "",
        duration_minutes: int = 60,
    ) -> FocusSession:
        """Starts a new focus session and enables notification suppression."""
        if self._active_session:
            # End previous session before starting new one
            self.end_focus_session(completed=False, notes="Switched to new focus session")

        # Resolve title if task_id provided
        if task_id and not task_title:
            task = self.store.get_task(task_id)
            if task:
                task_title = task.title
                project_id = project_id or task.project_id

        session = FocusSession(
            task_id=task_id,
            project_id=project_id,
            task_title=task_title or "Unspecified Focus Task",
            target_duration_minutes=duration_minutes,
            start_time=datetime.now(timezone.utc).isoformat(),
        )

        self._active_session = session
        self.store.save_focus_session(session)

        # Notify notification center to suppress distractions if supported
        if self.notification_center and hasattr(self.notification_center, "set_focus_mode"):
            self.notification_center.set_focus_mode(True)

        logger.info(f"Started focus session '{session.task_title}' ({duration_minutes}m)")
        return session

    def record_interruption(self) -> Optional[FocusSession]:
        """Increments the interruption counter for the active session."""
        if not self._active_session:
            return None
        self._active_session.interruptions += 1
        self.store.save_focus_session(self._active_session)
        return self._active_session

    def end_focus_session(
        self,
        completed: bool = True,
        notes: str = "",
    ) -> Optional[FocusSession]:
        """Ends the active focus session, calculates duration, and restores notifications."""
        if not self._active_session:
            return None

        session = self._active_session
        session.end_time = datetime.now(timezone.utc).isoformat()
        session.completed = completed
        if notes:
            session.notes = notes

        # Calculate actual minutes
        try:
            start_dt = datetime.fromisoformat(session.start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(session.end_time.replace("Z", "+00:00"))
            session.actual_duration_minutes = max(1, round((end_dt - start_dt).total_seconds() / 60))
        except Exception:
            session.actual_duration_minutes = session.target_duration_minutes

        self.store.save_focus_session(session)
        self._active_session = None

        if self.notification_center and hasattr(self.notification_center, "set_focus_mode"):
            self.notification_center.set_focus_mode(False)

        logger.info(f"Ended focus session '{session.task_title}' (Duration: {session.actual_duration_minutes}m)")
        return session
