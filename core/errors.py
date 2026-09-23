"""
SHIVANI Structured Error Hierarchy
Provides standardized typed exceptions with error codes, task tracking,
and actionable recovery suggestions.
"""

from typing import Optional, Dict, Any


class ShivaniError(Exception):
    """Base exception for all SHIVANI runtime errors."""

    def __init__(
        self,
        message: str,
        code: str = "ERR_INTERNAL",
        task_id: Optional[str] = None,
        recovery_suggestion: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.task_id = task_id
        self.recovery_suggestion = recovery_suggestion or "Inspect logs or retry with modified parameters."
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "task_id": self.task_id,
            "recovery_suggestion": self.recovery_suggestion,
            "details": self.details
        }


class ProviderError(ShivaniError):
    """Raised when an AI model provider call fails or returns unusable data."""

    def __init__(self, message: str, task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_PROVIDER_FAILURE",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or "Check API key, network connection, or switch to an alternate LLM provider.",
            **kwargs
        )


class ToolError(ShivaniError):
    """Raised when a tool encounters an execution failure."""

    def __init__(self, message: str, tool_name: Optional[str] = None, task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_TOOL_EXECUTION",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or f"Verify arguments and prerequisites for tool '{tool_name}'.",
            **kwargs
        )
        self.tool_name = tool_name


class PermissionDeniedError(ShivaniError):
    """Raised when an action is denied by permission policy or rejected by the user."""

    def __init__(self, message: str, task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_PERMISSION_DENIED",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or "Request explicit user approval or adjust security policy level.",
            **kwargs
        )


class ValidationError(ShivaniError):
    """Raised when input parameters, schemas, or LLM outputs fail validation."""

    def __init__(self, message: str, task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_VALIDATION_FAILURE",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or "Ensure input conforms to the expected Pydantic schema or re-prompt LLM.",
            **kwargs
        )


class VerificationError(ShivaniError):
    """Raised when environmental post-condition assertions fail."""

    def __init__(self, message: str, task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_VERIFICATION_FAILED",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or "Verify target window/process/file exists in the environment before concluding.",
            **kwargs
        )


class TaskCancelledError(ShivaniError):
    """Raised when a task is aborted by user command or emergency stop."""

    def __init__(self, message: str = "Task was cancelled by user or Emergency Stop", task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_TASK_CANCELLED",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or "Task was cleanly cancelled. Submit a new task when ready.",
            **kwargs
        )

