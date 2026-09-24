"""
SHIVANI Productivity OS Persistent Store (Phase 16).
Thread-safe SQLite storage for Goals, Milestones, Projects, Tasks,
Decisions, Requirements, Blockers, Focus Sessions, and Daily Plans.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional

from core.productivity.models import (
    Blocker,
    DailyPlan,
    Decision,
    FocusSession,
    Goal,
    Milestone,
    PersonalTask,
    Project,
    Requirement,
)

logger = logging.getLogger("shivani.productivity.store")


class ProductivityStore:
    """Persistent SQLite store for personal productivity OS."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_dir = Path.home() / ".shivani" / "data"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "productivity.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    target_date TEXT,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS milestones (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT,
                    project_id TEXT,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    target_date TEXT,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    owner TEXT,
                    codebase_path TEXT,
                    repo_url TEXT,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    project_id TEXT,
                    goal_id TEXT,
                    milestone_id TEXT,
                    due_date TEXT,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    topic TEXT NOT NULL,
                    status TEXT NOT NULL,
                    date TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requirements (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    req_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    verified INTEGER DEFAULT 0,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blockers (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS focus_sessions (
                    id TEXT PRIMARY KEY,
                    task_id TEXT,
                    project_id TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    completed INTEGER DEFAULT 0,
                    data JSON NOT NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_plans (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # Indexes for high performance querying
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_milestones_proj ON milestones(project_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blockers_status ON blockers(status);")

            conn.commit()

    # ==========================================================================
    # GOALS
    # ==========================================================================

    def save_goal(self, goal: Goal) -> None:
        with self._lock, self._get_connection() as conn:
            goal.updated_at = datetime.now(timezone.utc).isoformat()
            payload = goal.model_dump_json()
            conn.execute(
                """
                INSERT INTO goals (id, title, category, status, priority, progress, target_date, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    category = excluded.category,
                    status = excluded.status,
                    priority = excluded.priority,
                    progress = excluded.progress,
                    target_date = excluded.target_date,
                    data = excluded.data,
                    updated_at = excluded.updated_at;
                """,
                (
                    goal.id,
                    goal.title,
                    goal.category,
                    goal.status.value,
                    goal.priority.value,
                    goal.progress,
                    goal.target_date,
                    payload,
                    goal.created_at,
                    goal.updated_at,
                ),
            )
            conn.commit()

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM goals WHERE id = ?", (goal_id,))
            row = cursor.fetchone()
            if row:
                return Goal.model_validate_json(row["data"])
            return None

    def list_goals(self, status: Optional[str] = None) -> List[Goal]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT data FROM goals WHERE status = ? ORDER BY created_at DESC", (status,))
            else:
                cursor.execute("SELECT data FROM goals ORDER BY created_at DESC")
            return [Goal.model_validate_json(r["data"]) for r in cursor.fetchall()]

    def delete_goal(self, goal_id: str) -> bool:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==========================================================================
    # MILESTONES
    # ==========================================================================

    def save_milestone(self, milestone: Milestone) -> None:
        with self._lock, self._get_connection() as conn:
            milestone.updated_at = datetime.now(timezone.utc).isoformat()
            payload = milestone.model_dump_json()
            conn.execute(
                """
                INSERT INTO milestones (id, goal_id, project_id, title, status, progress, target_date, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    goal_id = excluded.goal_id,
                    project_id = excluded.project_id,
                    title = excluded.title,
                    status = excluded.status,
                    progress = excluded.progress,
                    target_date = excluded.target_date,
                    data = excluded.data,
                    updated_at = excluded.updated_at;
                """,
                (
                    milestone.id,
                    milestone.goal_id,
                    milestone.project_id,
                    milestone.title,
                    milestone.status.value,
                    milestone.progress,
                    milestone.target_date,
                    payload,
                    milestone.created_at,
                    milestone.updated_at,
                ),
            )
            conn.commit()

    def get_milestone(self, milestone_id: str) -> Optional[Milestone]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM milestones WHERE id = ?", (milestone_id,))
            row = cursor.fetchone()
            if row:
                return Milestone.model_validate_json(row["data"])
            return None

    def list_milestones(self, project_id: Optional[str] = None, goal_id: Optional[str] = None) -> List[Milestone]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if project_id and goal_id:
                cursor.execute("SELECT data FROM milestones WHERE project_id = ? AND goal_id = ?", (project_id, goal_id))
            elif project_id:
                cursor.execute("SELECT data FROM milestones WHERE project_id = ?", (project_id,))
            elif goal_id:
                cursor.execute("SELECT data FROM milestones WHERE goal_id = ?", (goal_id,))
            else:
                cursor.execute("SELECT data FROM milestones")
            return [Milestone.model_validate_json(r["data"]) for r in cursor.fetchall()]

    def delete_milestone(self, milestone_id: str) -> bool:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM milestones WHERE id = ?", (milestone_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==========================================================================
    # PROJECTS
    # ==========================================================================

    def save_project(self, project: Project) -> None:
        with self._lock, self._get_connection() as conn:
            project.updated_at = datetime.now(timezone.utc).isoformat()
            payload = project.model_dump_json()
            conn.execute(
                """
                INSERT INTO projects (id, name, status, priority, owner, codebase_path, repo_url, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    status = excluded.status,
                    priority = excluded.priority,
                    owner = excluded.owner,
                    codebase_path = excluded.codebase_path,
                    repo_url = excluded.repo_url,
                    data = excluded.data,
                    updated_at = excluded.updated_at;
                """,
                (
                    project.id,
                    project.name,
                    project.status.value,
                    project.priority.value,
                    project.owner,
                    project.codebase_path,
                    project.repo_url,
                    payload,
                    project.created_at,
                    project.updated_at,
                ),
            )
            conn.commit()

    def get_project(self, project_id: str) -> Optional[Project]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if row:
                return Project.model_validate_json(row["data"])
            return None

    def get_project_by_name(self, name: str) -> Optional[Project]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM projects WHERE LOWER(name) = LOWER(?)", (name.strip(),))
            row = cursor.fetchone()
            if row:
                return Project.model_validate_json(row["data"])
            return None

    def list_projects(self, status: Optional[str] = None) -> List[Project]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT data FROM projects WHERE status = ? ORDER BY created_at DESC", (status,))
            else:
                cursor.execute("SELECT data FROM projects ORDER BY created_at DESC")
            return [Project.model_validate_json(r["data"]) for r in cursor.fetchall()]

    def delete_project(self, project_id: str) -> bool:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==========================================================================
    # TASKS
    # ==========================================================================

    def save_task(self, task: PersonalTask) -> None:
        with self._lock, self._get_connection() as conn:
            task.updated_at = datetime.now(timezone.utc).isoformat()
            payload = task.model_dump_json()
            conn.execute(
                """
                INSERT INTO tasks (id, title, status, priority, project_id, goal_id, milestone_id, due_date, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    status = excluded.status,
                    priority = excluded.priority,
                    project_id = excluded.project_id,
                    goal_id = excluded.goal_id,
                    milestone_id = excluded.milestone_id,
                    due_date = excluded.due_date,
                    data = excluded.data,
                    updated_at = excluded.updated_at;
                """,
                (
                    task.id,
                    task.title,
                    task.status.value,
                    task.priority.value,
                    task.project_id,
                    task.goal_id,
                    task.milestone_id,
                    task.due_date,
                    payload,
                    task.created_at,
                    task.updated_at,
                ),
            )
            conn.commit()

    def get_task(self, task_id: str) -> Optional[PersonalTask]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if row:
                return PersonalTask.model_validate_json(row["data"])
            return None

    def list_tasks(
        self,
        project_id: Optional[str] = None,
        goal_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[PersonalTask]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT data FROM tasks WHERE 1=1"
            params: List[Any] = []
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            if goal_id:
                query += " AND goal_id = ?"
                params.append(goal_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY created_at DESC"
            cursor.execute(query, tuple(params))
            return [PersonalTask.model_validate_json(r["data"]) for r in cursor.fetchall()]

    def delete_task(self, task_id: str) -> bool:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==========================================================================
    # DECISIONS
    # ==========================================================================

    def save_decision(self, decision: Decision) -> None:
        with self._lock, self._get_connection() as conn:
            payload = decision.model_dump_json()
            conn.execute(
                """
                INSERT INTO decisions (id, project_id, topic, status, date, data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    topic = excluded.topic,
                    status = excluded.status,
                    date = excluded.date,
                    data = excluded.data;
                """,
                (
                    decision.id,
                    decision.project_id,
                    decision.topic,
                    decision.status.value,
                    decision.date,
                    payload,
                    decision.created_at,
                ),
            )
            conn.commit()

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM decisions WHERE id = ?", (decision_id,))
            row = cursor.fetchone()
            if row:
                return Decision.model_validate_json(row["data"])
            return None

    def list_decisions(self, project_id: Optional[str] = None) -> List[Decision]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute("SELECT data FROM decisions WHERE project_id = ? ORDER BY date DESC", (project_id,))
            else:
                cursor.execute("SELECT data FROM decisions ORDER BY date DESC")
            return [Decision.model_validate_json(r["data"]) for r in cursor.fetchall()]

    # ==========================================================================
    # REQUIREMENTS
    # ==========================================================================

    def save_requirement(self, req: Requirement) -> None:
        with self._lock, self._get_connection() as conn:
            payload = req.model_dump_json()
            conn.execute(
                """
                INSERT INTO requirements (id, project_id, req_id, status, verified, data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    req_id = excluded.req_id,
                    status = excluded.status,
                    verified = excluded.verified,
                    data = excluded.data;
                """,
                (
                    req.id,
                    req.project_id,
                    req.req_id,
                    req.status.value,
                    1 if req.verified else 0,
                    payload,
                    req.created_at,
                ),
            )
            conn.commit()

    def list_requirements(self, project_id: Optional[str] = None) -> List[Requirement]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute("SELECT data FROM requirements WHERE project_id = ? ORDER BY req_id ASC", (project_id,))
            else:
                cursor.execute("SELECT data FROM requirements ORDER BY req_id ASC")
            return [Requirement.model_validate_json(r["data"]) for r in cursor.fetchall()]

    # ==========================================================================
    # BLOCKERS
    # ==========================================================================

    def save_blocker(self, blocker: Blocker) -> None:
        with self._lock, self._get_connection() as conn:
            payload = blocker.model_dump_json()
            conn.execute(
                """
                INSERT INTO blockers (id, project_id, title, status, data, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    status = excluded.status,
                    data = excluded.data;
                """,
                (
                    blocker.id,
                    blocker.project_id,
                    blocker.title,
                    blocker.status.value,
                    payload,
                    blocker.created_at,
                ),
            )
            conn.commit()

    def get_blocker(self, blocker_id: str) -> Optional[Blocker]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM blockers WHERE id = ?", (blocker_id,))
            row = cursor.fetchone()
            if row:
                return Blocker.model_validate_json(row["data"])
            return None

    def list_blockers(self, project_id: Optional[str] = None, status: Optional[str] = None) -> List[Blocker]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT data FROM blockers WHERE 1=1"
            params: List[Any] = []
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY created_at DESC"
            cursor.execute(query, tuple(params))
            return [Blocker.model_validate_json(r["data"]) for r in cursor.fetchall()]

    # ==========================================================================
    # FOCUS SESSIONS
    # ==========================================================================

    def save_focus_session(self, session: FocusSession) -> None:
        with self._lock, self._get_connection() as conn:
            payload = session.model_dump_json()
            conn.execute(
                """
                INSERT INTO focus_sessions (id, task_id, project_id, start_time, end_time, completed, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    end_time = excluded.end_time,
                    completed = excluded.completed,
                    data = excluded.data;
                """,
                (
                    session.id,
                    session.task_id,
                    session.project_id,
                    session.start_time,
                    session.end_time,
                    1 if session.completed else 0,
                    payload,
                ),
            )
            conn.commit()

    def list_focus_sessions(self, limit: int = 50) -> List[FocusSession]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM focus_sessions ORDER BY start_time DESC LIMIT ?", (limit,))
            return [FocusSession.model_validate_json(r["data"]) for r in cursor.fetchall()]

    # ==========================================================================
    # DAILY PLANS
    # ==========================================================================

    def save_daily_plan(self, plan: DailyPlan) -> None:
        with self._lock, self._get_connection() as conn:
            payload = plan.model_dump_json()
            conn.execute(
                """
                INSERT INTO daily_plans (id, date, status, data, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    data = excluded.data;
                """,
                (
                    plan.id,
                    plan.date,
                    plan.status.value,
                    payload,
                    plan.created_at,
                ),
            )
            conn.commit()

    def get_daily_plan(self, date_str: str) -> Optional[DailyPlan]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM daily_plans WHERE date = ? ORDER BY created_at DESC LIMIT 1", (date_str,))
            row = cursor.fetchone()
            if row:
                return DailyPlan.model_validate_json(row["data"])
            return None

    def list_daily_plans(self, limit: int = 30) -> List[DailyPlan]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM daily_plans ORDER BY date DESC LIMIT ?", (limit,))
            return [DailyPlan.model_validate_json(r["data"]) for r in cursor.fetchall()]
