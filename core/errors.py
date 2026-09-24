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
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.task_id = task_id
        self.recovery_suggestion = recovery_suggestion or "Inspect logs or retry with modified parameters."
        self.details = details or {}
        self.recoverable = recoverable
        self.retryable = retryable

    @property
    def error_code(self) -> str:
        """Alias for code."""
        return self.code

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.__class__.__name__,
            "code": self.code,
            "error_code": self.code,
            "message": self.message,
            "task_id": self.task_id,
            "recovery_suggestion": self.recovery_suggestion,
            "details": self.details,
            "recoverable": self.recoverable,
            "retryable": self.retryable,
        }


class ProviderError(ShivaniError):
    """Raised when an AI model provider call fails or returns unusable data."""

    def __init__(self, message: str, task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, retryable: bool = True, **kwargs):
        super().__init__(
            message=message,
            code="ERR_PROVIDER_FAILURE",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or "Check API key, network connection, or switch to an alternate LLM provider.",
            recoverable=True,
            retryable=retryable,
            **kwargs
        )


class ToolError(ShivaniError):
    """Raised when a tool encounters an execution failure."""

    def __init__(self, message: str, tool_name: Optional[str] = None, task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, retryable: bool = False, **kwargs):
        super().__init__(
            message=message,
            code="ERR_TOOL_EXECUTION",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or f"Verify arguments and prerequisites for tool '{tool_name}'.",
            recoverable=True,
            retryable=retryable,
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
            recoverable=False,
            retryable=False,
            **kwargs
        )


class SecurityViolation(ShivaniError):
    """Raised when a security policy or boundary is violated (prompt injection, path traversal, sandbox)."""

    def __init__(self, message: str, violation_type: str = "SECURITY_VIOLATION", task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code=f"ERR_SECURITY_{violation_type.upper()}",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or "Action blocked by security policy. Check audit logs.",
            recoverable=False,
            retryable=False,
            details={"violation_type": violation_type, **kwargs.get("details", {})},
        )
        self.violation_type = violation_type


class AuthenticationRequiredError(ShivaniError):
    """Raised when an operation requires user authentication or elevation."""

    def __init__(self, message: str = "Authentication or elevation required for this operation", task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_AUTH_REQUIRED",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or "Authenticate the session or provide credentials via vault.",
            recoverable=True,
            retryable=False,
            **kwargs
        )


class BrowserError(ShivaniError):
    """Raised when browser automation encounters an error (element not found, navigation timeout)."""

    def __init__(self, message: str, task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, retryable: bool = True, **kwargs):
        super().__init__(
            message=message,
            code="ERR_BROWSER_AUTOMATION",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or "Verify page state, selector, or ensure browser is running.",
            recoverable=True,
            retryable=retryable,
            **kwargs
        )


class PhoneDisconnectedError(ShivaniError):
    """Raised when connection to the Android companion phone is lost or unavailable."""

    def __init__(self, message: str = "Android device is disconnected or unreachable", task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_PHONE_DISCONNECTED",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or "Check phone Wi-Fi connection and ensure Shivani Mobile service is active.",
            recoverable=True,
            retryable=True,
            **kwargs
        )


class RateLimitError(ShivaniError):
    """Raised when an API or provider rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: float = 5.0, task_id: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_RATE_LIMITED",
            task_id=task_id,
            recovery_suggestion=f"Wait {retry_after}s before retrying operation.",
            recoverable=True,
            retryable=True,
            details={"retry_after": retry_after, **kwargs.get("details", {})},
        )
        self.retry_after = retry_after


class TimeoutError(ShivaniError):
    """Raised when an operation exceeds its configured execution limit timeout."""

    def __init__(self, message: str = "Operation timed out", timeout_seconds: float = 0.0, task_id: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_TIMEOUT",
            task_id=task_id,
            recovery_suggestion="Consider increasing timeout limit or simplifying the task.",
            recoverable=True,
            retryable=False,
            details={"timeout_seconds": timeout_seconds, **kwargs.get("details", {})},
        )
        self.timeout_seconds = timeout_seconds


class IdempotencyConflictError(ShivaniError):
    """Raised when a non-idempotent operation is attempted with duplicate key."""

    def __init__(self, message: str = "Duplicate operation detected by idempotency manager", task_id: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_IDEMPOTENCY_CONFLICT",
            task_id=task_id,
            recovery_suggestion="Use cached result or supply a fresh idempotency key.",
            recoverable=True,
            retryable=False,
            **kwargs
        )


class SandboxViolationError(ShivaniError):
    """Raised when a sandboxed execution attempts prohibited system calls or network access."""

    def __init__(self, message: str, task_id: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="ERR_SANDBOX_VIOLATION",
            task_id=task_id,
            recovery_suggestion="Review command and sandbox policy restrictions.",
            recoverable=False,
            retryable=False,
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
            recoverable=True,
            retryable=False,
            **kwargs
        )


class VerificationError(ShivaniError):
    """Raised when environmental post-condition assertions fail."""

    def __init__(self, message: str, task_id: Optional[str] = None, recovery_suggestion: Optional[str] = None, retryable: bool = True, **kwargs):
        super().__init__(
            message=message,
            code="ERR_VERIFICATION_FAILED",
            task_id=task_id,
            recovery_suggestion=recovery_suggestion or "Verify target window/process/file exists in the environment before concluding.",
            recoverable=True,
            retryable=retryable,
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
            recoverable=False,
            retryable=False,
            **kwargs
        )

