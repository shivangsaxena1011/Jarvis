"""
SHIVANI Skill Sandbox
Enforces runtime isolation, execution timeouts, filesystem boundary containment,
network domain restrictions, and crash containment for dynamic skills.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set
from urllib.parse import urlparse

from core.utils.result import Result
from security.permissions.models import RiskLevel
from skills.manifest import SkillManifest
from skills.models import SkillHealth, SkillTelemetry

logger = logging.getLogger("shivani.skills.sandbox")


class SandboxSecurityError(PermissionError):
    """Raised when a sandboxed skill violates sandbox security policies."""
    pass


class SkillSandbox:
    """Executes skill actions and tools within security boundaries."""

    def __init__(
        self,
        manifest: SkillManifest,
        allowed_paths: Optional[List[Path]] = None,
        allowed_domains: Optional[List[str]] = None,
        default_timeout_sec: float = 30.0,
    ):
        self.manifest = manifest
        self.allowed_paths: List[Path] = [p.resolve() for p in (allowed_paths or [])]
        self.allowed_domains: Set[str] = set(allowed_domains or [])
        self.default_timeout_sec = (
            float(manifest.policies.timeout_seconds)
            if manifest.policies and manifest.policies.timeout_seconds
            else default_timeout_sec
        )
        self.telemetry = SkillTelemetry()

    def add_allowed_path(self, path: Path) -> None:
        """Grants access to a directory or file path."""
        self.allowed_paths.append(path.resolve())

    def add_allowed_domain(self, domain: str) -> None:
        """Grants access to a network domain."""
        self.allowed_domains.add(domain.lower())

    def validate_path_access(self, target_path: Path, write: bool = False) -> None:
        """Verifies if path is within allowed directories."""
        resolved = target_path.resolve()
        for allowed in self.allowed_paths:
            try:
                resolved.relative_to(allowed)
                return  # Access allowed
            except ValueError:
                continue

        # If not matched
        op = "write to" if write else "read from"
        msg = f"Skill '{self.manifest.name}' attempted to {op} unauthorized path: {resolved}"
        logger.warning(msg)
        raise SandboxSecurityError(msg)

    def validate_network_access(self, url: str) -> None:
        """Verifies if URL hostname is in allowed domains."""
        if "*" in self.allowed_domains:
            return  # Unrestricted outbound if explicitly permitted

        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            raise SandboxSecurityError(f"Invalid URL for network access check: {url}")

        for domain in self.allowed_domains:
            if hostname == domain or hostname.endswith("." + domain):
                return

        msg = f"Skill '{self.manifest.name}' attempted to access unauthorized domain: {hostname}"
        logger.warning(msg)
        raise SandboxSecurityError(msg)

    async def execute_coroutine(
        self,
        coro_func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Result[Any, Exception]:
        """
        Executes a coroutine inside the sandbox with timeout and crash containment.
        Returns Result.ok(data) or Result.err(exception).
        """
        effective_timeout = timeout or self.default_timeout_sec
        start_time = time.perf_counter()

        self.telemetry.invocations += 1

        try:
            res = await asyncio.wait_for(
                coro_func(*args, **kwargs),
                timeout=effective_timeout,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.telemetry.last_latency_ms = elapsed_ms
            # Running average
            if self.telemetry.average_latency_ms == 0.0:
                self.telemetry.average_latency_ms = elapsed_ms
            else:
                self.telemetry.average_latency_ms = (
                    0.8 * self.telemetry.average_latency_ms + 0.2 * elapsed_ms
                )
            return Result.ok(res)

        except asyncio.TimeoutError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.telemetry.errors += 1
            self.telemetry.last_error = f"Execution timed out after {effective_timeout}s"
            logger.error(f"Skill '{self.manifest.name}' timed out after {effective_timeout}s")
            return Result.err(TimeoutError(f"Skill execution timed out after {effective_timeout}s"))

        except SandboxSecurityError as e:
            self.telemetry.errors += 1
            self.telemetry.last_error = str(e)
            logger.error(f"Sandbox security violation in skill '{self.manifest.name}': {e}")
            return Result.err(e)

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.telemetry.errors += 1
            self.telemetry.last_error = f"{type(e).__name__}: {str(e)}"
            logger.exception(f"Unhandled exception in sandboxed skill '{self.manifest.name}': {e}")
            return Result.err(e)

    def execute_sync(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Result[Any, Exception]:
        """Executes a synchronous function with crash containment."""
        start_time = time.perf_counter()
        self.telemetry.invocations += 1

        try:
            res = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.telemetry.last_latency_ms = elapsed_ms
            return Result.ok(res)
        except SandboxSecurityError as e:
            self.telemetry.errors += 1
            self.telemetry.last_error = str(e)
            return Result.err(e)
        except Exception as e:
            self.telemetry.errors += 1
            self.telemetry.last_error = f"{type(e).__name__}: {str(e)}"
            return Result.err(e)
