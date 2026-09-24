"""
SHIVANI Completion Verification Gate (Phase 16).
Ensures tasks are only marked COMPLETED when real deliverables exist,
artifacts are verified on disk, tests have passed, or user confirmation is given.
Never permits fabricated or unverified completion.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from core.productivity.models import PersonalTask, TaskStatus

logger = logging.getLogger("shivani.productivity.verification_gate")


class TaskCompletionGate:
    """Verifies conditions and outcomes before permitting a task to transition to COMPLETED."""

    @classmethod
    def verify_completion(
        cls,
        task: PersonalTask,
        execution_output: Optional[Dict[str, Any]] = None,
        require_artifact_check: bool = True,
    ) -> Tuple[bool, List[str]]:
        """
        Validates whether a task meets completion criteria:
        1. Artifacts declared on task or execution output actually exist on disk.
        2. If tests were required by metadata, verifies tests passed.
        3. Checks for explicit error flags or failed sub-actions.
        Returns (is_verified, list_of_verification_failures).
        """
        failures: List[str] = []
        exec_data = execution_output or {}

        # 1. Error check in execution output
        if exec_data.get("error"):
            failures.append(f"Execution returned error: {exec_data.get('error')}")

        if exec_data.get("success") is False:
            failures.append("Execution recorded success = False")

        # 2. Artifact Existence Verification
        artifacts_to_check: List[str] = list(task.artifacts)
        if "artifact_path" in exec_data:
            artifacts_to_check.append(str(exec_data["artifact_path"]))
        if "artifacts" in exec_data and isinstance(exec_data["artifacts"], list):
            artifacts_to_check.extend([str(a) for a in exec_data["artifacts"]])

        if require_artifact_check and artifacts_to_check:
            missing_artifacts: List[str] = []
            for art in artifacts_to_check:
                # If it's a file path, verify it exists
                p = Path(art)
                if ("/" in art or "\\" in art) and not p.exists():
                    missing_artifacts.append(art)

            if missing_artifacts:
                failures.append(f"Declared artifact(s) do not exist on disk: {missing_artifacts}")

        # 3. Test verification check if task context requires passing tests
        if task.context.get("requires_tests_pass", False):
            tests_passed = exec_data.get("tests_passed", task.context.get("tests_passed", False))
            if not tests_passed:
                failures.append("Task requires passing automated tests, but no test pass verification was recorded.")

        # 4. Empty/Unperformed check
        if not exec_data and not task.artifacts and not task.notes:
            # If no work evidence was attached, require at least an explicit confirmation
            if not task.context.get("manually_confirmed", False):
                failures.append("No execution output, notes, or artifacts were supplied to verify completion.")

        is_verified = len(failures) == 0
        return is_verified, failures
