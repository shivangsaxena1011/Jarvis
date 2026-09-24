"""
SHIVANI Result Monad
Functional error handling primitive for robust operation returns.
"""

from typing import Any, Callable, Generic, Optional, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


class Result(Generic[T, E]):
    """Represents either a success (Ok) or a failure (Err)."""

    def __init__(self, is_ok: bool, value: Optional[T] = None, error: Optional[E] = None):
        self._is_ok = is_ok
        self._value = value
        self._error = error

    @classmethod
    def ok(cls, value: T) -> "Result[T, Any]":
        return cls(is_ok=True, value=value, error=None)

    @classmethod
    def err(cls, error: E) -> "Result[Any, E]:":
        return cls(is_ok=False, value=None, error=error)

    @property
    def is_ok(self) -> bool:
        return self._is_ok

    @property
    def is_err(self) -> bool:
        return not self._is_ok

    def unwrap(self) -> T:
        """Returns value if Ok, raises ValueError if Err."""
        if not self._is_ok:
            raise ValueError(f"Called unwrap on Err Result: {self._error}")
        return self._value  # type: ignore

    def unwrap_err(self) -> E:
        """Returns error if Err, raises ValueError if Ok."""
        if self._is_ok:
            raise ValueError(f"Called unwrap_err on Ok Result: {self._value}")
        return self._error  # type: ignore

    def unwrap_or(self, default: T) -> T:
        if self._is_ok:
            return self._value  # type: ignore
        return default

    def map(self, fn: Callable[[T], U]) -> "Result[U, E]":
        if self._is_ok:
            return Result.ok(fn(self._value))  # type: ignore
        return Result.err(self._error)  # type: ignore

    def __repr__(self) -> str:
        if self._is_ok:
            return f"Ok({repr(self._value)})"
        return f"Err({repr(self._error)})"

    def __bool__(self) -> bool:
        return self._is_ok
