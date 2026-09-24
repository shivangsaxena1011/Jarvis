"""
SHIVANI Error Analyzer
Parses and categorizes build, test, and runtime failures into actionable diagnostic domains:
syntax, dependency, type, runtime, configuration, network, database, or environment.
"""

import re
from typing import List, Optional

from agents.coding.models import ErrorCategory, ErrorDiagnosis


class ErrorAnalyzer:
    """Diagnoses root causes from execution failure logs and prescribes fixes."""

    def analyze_error(self, error_log: str, command: str = "") -> ErrorDiagnosis:
        """Classifies error and extracts actionable remediation steps."""
        text = error_log.strip()
        lower_text = text.lower()

        missing_packages: List[str] = []

        # 1. Dependency Failures
        mod_match = re.search(r"No module named ['\"]([^'\"]+)['\"]", text)
        if mod_match:
            pkg = mod_match.group(1).split(".")[0]
            missing_packages.append(pkg)
            return ErrorDiagnosis(
                category=ErrorCategory.DEPENDENCY,
                root_cause=f"Missing Python package/module '{pkg}'",
                error_summary=f"ModuleNotFoundError: No module named '{pkg}'",
                suggested_action=f"Install dependency using package manager: uv pip install {pkg} or add to requirements.",
                missing_packages=[pkg],
                requires_confirmation=True
            )

        node_mod_match = re.search(r"Cannot find module ['\"]([^'\"]+)['\"]", text)
        if node_mod_match:
            pkg = node_mod_match.group(1)
            missing_packages.append(pkg)
            return ErrorDiagnosis(
                category=ErrorCategory.DEPENDENCY,
                root_cause=f"Missing Node.js package '{pkg}'",
                error_summary=f"Cannot find module '{pkg}'",
                suggested_action=f"Install dependency using package manager: npm install {pkg}",
                missing_packages=[pkg],
                requires_confirmation=True
            )

        # 2. Syntax Failures
        if "syntaxerror" in lower_text or "indentationerror" in lower_text or "unexpected token" in lower_text:
            line_match = re.search(r"line\s+(\d+)", lower_text)
            line_info = f" around line {line_match.group(1)}" if line_match else ""
            return ErrorDiagnosis(
                category=ErrorCategory.SYNTAX,
                root_cause=f"Syntax error{line_info}",
                error_summary="Code violates language grammar rules or has malformed indentation.",
                suggested_action="Review and patch the syntax error or invalid token at the specified line.",
                requires_confirmation=False
            )

        # 3. Type Errors
        if "typeerror" in lower_text or "attributeerror" in lower_text or "ts(" in lower_text:
            return ErrorDiagnosis(
                category=ErrorCategory.TYPE_ERROR,
                root_cause="Type mismatch or invalid attribute access",
                error_summary="Object is accessed with incompatible type or missing member.",
                suggested_action="Inspect attribute names, function signature, or TypeScript types.",
                requires_confirmation=False
            )

        # 4. Database Errors
        if any(w in lower_text for w in ["operationalerror", "relation", "does not exist", "database", "connection refused", "port 5432", "port 3306", "port 27017"]):
            return ErrorDiagnosis(
                category=ErrorCategory.DATABASE,
                root_cause="Database connection failure or missing database schema/table",
                error_summary="Cannot connect to database or referenced table/column does not exist.",
                suggested_action="Ensure database container/service is running and run database migrations.",
                requires_confirmation=False
            )

        # 5. Network / Timeout Errors
        if any(w in lower_text for w in ["connectionrefused", "timed out", "econnrefused", "network error", "dns resolution failed"]):
            return ErrorDiagnosis(
                category=ErrorCategory.NETWORK,
                root_cause="Network unreachable or connection refused",
                error_summary="Target host or port is not responding.",
                suggested_action="Check network connectivity and ensure the target service/server is listening.",
                requires_confirmation=False
            )

        # 6. Configuration / Missing File
        if "filenotfounderror" in lower_text or "no such file or directory" in lower_text or "enoent" in lower_text:
            return ErrorDiagnosis(
                category=ErrorCategory.CONFIGURATION,
                root_cause="Missing file, configuration, or environment variable",
                error_summary="Application expected a file that is absent.",
                suggested_action="Verify path references, copy .env.example if needed, or create missing file.",
                requires_confirmation=False
            )

        # 7. Generic Runtime
        return ErrorDiagnosis(
            category=ErrorCategory.RUNTIME,
            root_cause="Unhandled runtime exception",
            error_summary=text[:300] if text else "Unknown execution failure.",
            suggested_action="Examine stack trace, add exception handling, and verify inputs.",
            requires_confirmation=False
        )
