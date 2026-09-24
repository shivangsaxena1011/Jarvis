"""
SHIVANI Smart Retry Policy
Implements exponential backoff with jitter and pre-verification checks
to ensure safe, non-destructive re-execution of recoverable operations.
"""

import asyncio
import logging
import random
from typing import Any, Callable, Coroutine, Optional, TypeVar

from core.errors import ShivaniError

logger = logging.getLogger("shivani.retry")

T = TypeVar("T")


class SmartRetryPolicy:
    """
    Intelligent retry controller that evaluates error retryability,
    performs pre-verification to avoid duplicate work, and applies
    exponential backoff with jitter.
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    def compute_delay(self, attempt: int) -> float:
        """Computes exponential backoff delay with optional jitter."""
        delay = min(self.max_delay, self.initial_delay * (self.backoff_factor ** attempt))
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        return max(0.1, delay)

    def is_retryable(self, exception: Exception) -> bool:
        """Determines if an exception qualifies for automated retry."""
        if isinstance(exception, ShivaniError):
            return exception.retryable
        # Standard system transient exceptions
        if isinstance(exception, (TimeoutError, ConnectionError, OSError)):
            return True
        return False

    async def execute_with_retry(
        self,
        operation: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        pre_verify: Optional[Callable[..., Coroutine[Any, Any, bool]]] = None,
        operation_name: str = "operation",
        **kwargs: Any,
    ) -> T:
        """
        Executes an async operation with retry logic.
        If pre_verify is supplied and returns True before any attempt,
        the operation is considered already satisfied and skipped.
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            if attempt > 0 and pre_verify is not None:
                try:
                    logger.info("Running pre-verification before retry attempt %d for %s", attempt, operation_name)
                    already_satisfied = await pre_verify(*args, **kwargs)
                    if already_satisfied:
                        logger.info("Pre-verification passed: %s already achieved, skipping retry", operation_name)
                        # Return None or appropriate completed state if pre-verified
                        return True  # type: ignore
                except Exception as pv_err:
                    logger.warning("Pre-verification error: %s", pv_err)

            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt >= self.max_retries or not self.is_retryable(e):
                    logger.warning(
                        "Operation %s failed on attempt %d/%d (retryable=%s): %s",
                        operation_name, attempt + 1, self.max_retries + 1, self.is_retryable(e), e
                    )
                    raise

                delay = self.compute_delay(attempt)
                logger.warning(
                    "Operation %s failed with %s (attempt %d/%d). Retrying in %.2fs...",
                    operation_name, e, attempt + 1, self.max_retries + 1, delay
                )
                await asyncio.sleep(delay)

        if last_exception:
            raise last_exception
        raise RuntimeError(f"Retry loop exhausted for {operation_name}")
