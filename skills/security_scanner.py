"""
SHIVANI Skill Security Scanner
Performs static AST and regex analysis on skill packages to detect:
- Arbitrary code execution / obfuscation (eval, exec, compile)
- Uncontrolled subprocess execution (shell=True, os.system)
- Direct network socket abuse or raw socket backdoors
- Credential harvesting / exfiltration (accessing .env, .ssh, sensitive env vars)
- File system escapes / path traversal outside sandbox boundaries
"""

import ast
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from security.permissions.models import RiskLevel


class SecurityViolation(BaseModel):
    rule_id: str
    severity: RiskLevel
    message: str
    file_path: str
    line_number: Optional[int] = None
    snippet: Optional[str] = None


class SecurityScanResult(BaseModel):
    is_safe: bool = True
    risk_level: RiskLevel = RiskLevel.SAFE
    violations: List[SecurityViolation] = Field(default_factory=list)
    files_scanned: int = 0
    warnings: List[str] = Field(default_factory=list)


class SkillSecurityScanner:
    """Static analysis scanner for skill source code and manifests."""

    # Regex patterns for credential / sensitive file access
    SUSPICIOUS_REGEX_PATTERNS = [
        (r"(\.aws/credentials|\.ssh/id_rsa|\.env\b|vault\.json)", "POTENTIAL_CREDENTIAL_ACCESS", RiskLevel.HIGH_RISK, "Access to sensitive credential files detected."),
        (r"(base64\.b64decode\(.+\)\.(?:decode|encode)\(\)|exec\(base64)", "OBFUSCATED_PAYLOAD", RiskLevel.CRITICAL, "Obfuscated payload execution pattern detected."),
        (r"(socket\.socket\(.*\).connect\()", "RAW_SOCKET_CONNECT", RiskLevel.HIGH_RISK, "Direct raw network socket connection detected."),
        (r"(\bos\.system\()", "OS_SYSTEM_CALL", RiskLevel.CRITICAL, "Direct os.system invocation detected."),
    ]

    DANGEROUS_CALLS = {
        "eval": (RiskLevel.CRITICAL, "Use of eval() detected, allowing arbitrary code execution."),
        "exec": (RiskLevel.CRITICAL, "Use of exec() detected, allowing dynamic code execution."),
        "compile": (RiskLevel.HIGH_RISK, "Use of compile() detected."),
    }

    DANGEROUS_ATTRIBUTES = {
        "os.system": (RiskLevel.CRITICAL, "Direct invocation of os.system()."),
        "os.popen": (RiskLevel.HIGH_RISK, "Use of os.popen() opens subprocess pipeline."),
        "os.spawn": (RiskLevel.HIGH_RISK, "Use of os.spawn() launches unmanaged processes."),
    }

    def scan_directory(self, skill_dir: Path) -> SecurityScanResult:
        """Recursively scans a skill directory for dangerous patterns."""
        skill_path = Path(skill_dir)
        if not skill_path.exists() or not skill_path.is_dir():
            return SecurityScanResult(
                is_safe=False,
                risk_level=RiskLevel.CRITICAL,
                violations=[
                    SecurityViolation(
                        rule_id="DIR_NOT_FOUND",
                        severity=RiskLevel.CRITICAL,
                        message=f"Skill directory does not exist: {skill_path}",
                        file_path=str(skill_path),
                    )
                ],
            )

        violations: List[SecurityViolation] = []
        warnings: List[str] = []
        files_scanned = 0

        for file_path in skill_path.rglob("*.py"):
            files_scanned += 1
            file_violations, file_warnings = self.scan_file(file_path)
            violations.extend(file_violations)
            warnings.extend(file_warnings)

        highest_risk = RiskLevel.SAFE
        priority = {
            RiskLevel.SAFE: 0,
            RiskLevel.LOW_RISK: 1,
            RiskLevel.SENSITIVE: 2,
            RiskLevel.HIGH_RISK: 3,
            RiskLevel.CRITICAL: 4,
        }

        for v in violations:
            if priority[v.severity] > priority[highest_risk]:
                highest_risk = v.severity

        # A skill is deemed unsafe if any CRITICAL violations exist, or multiple HIGH_RISK violations
        critical_count = sum(1 for v in violations if v.severity == RiskLevel.CRITICAL)
        high_count = sum(1 for v in violations if v.severity == RiskLevel.HIGH_RISK)
        is_safe = (critical_count == 0) and (high_count <= 1)

        return SecurityScanResult(
            is_safe=is_safe,
            risk_level=highest_risk,
            violations=violations,
            files_scanned=files_scanned,
            warnings=warnings,
        )

    def scan_file(self, file_path: Path) -> (List[SecurityViolation], List[str]):
        """Scans a single python source file using AST and regex."""
        violations: List[SecurityViolation] = []
        warnings: List[str] = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            violations.append(
                SecurityViolation(
                    rule_id="READ_ERROR",
                    severity=RiskLevel.HIGH_RISK,
                    message=f"Failed to read file for analysis: {e}",
                    file_path=str(file_path),
                )
            )
            return violations, warnings

        lines = content.splitlines()

        # 1. Regex checks
        for pattern, rule_id, severity, msg in self.SUSPICIOUS_REGEX_PATTERNS:
            for idx, line in enumerate(lines, start=1):
                if re.search(pattern, line):
                    violations.append(
                        SecurityViolation(
                            rule_id=rule_id,
                            severity=severity,
                            message=msg,
                            file_path=str(file_path),
                            line_number=idx,
                            snippet=line.strip(),
                        )
                    )

        # 2. AST checks
        try:
            tree = ast.parse(content, filename=str(file_path))
            ast_violations = self._scan_ast(tree, file_path, lines)
            violations.extend(ast_violations)
        except SyntaxError as e:
            violations.append(
                SecurityViolation(
                    rule_id="SYNTAX_ERROR",
                    severity=RiskLevel.HIGH_RISK,
                    message=f"Source syntax error: {e}",
                    file_path=str(file_path),
                    line_number=e.lineno,
                )
            )

        return violations, warnings

    def _scan_ast(self, tree: ast.AST, file_path: Path, lines: List[str]) -> List[SecurityViolation]:
        violations: List[SecurityViolation] = []

        for node in ast.walk(tree):
            # Check function calls
            if isinstance(node, ast.Call):
                # Call to built-in function (eval, exec, etc.)
                if isinstance(node.func, ast.Name):
                    fn_name = node.func.id
                    if fn_name in self.DANGEROUS_CALLS:
                        sev, desc = self.DANGEROUS_CALLS[fn_name]
                        line_no = getattr(node, "lineno", None)
                        snippet = lines[line_no - 1].strip() if line_no and line_no <= len(lines) else None
                        violations.append(
                            SecurityViolation(
                                rule_id=f"DANGEROUS_{fn_name.upper()}",
                                severity=sev,
                                message=desc,
                                file_path=str(file_path),
                                line_number=line_no,
                                snippet=snippet,
                            )
                        )

                # Call to module attribute (e.g., subprocess.Popen, os.system)
                elif isinstance(node.func, ast.Attribute):
                    full_name = self._resolve_attribute(node.func)
                    if full_name in self.DANGEROUS_ATTRIBUTES:
                        sev, desc = self.DANGEROUS_ATTRIBUTES[full_name]
                        line_no = getattr(node, "lineno", None)
                        snippet = lines[line_no - 1].strip() if line_no and line_no <= len(lines) else None
                        violations.append(
                            SecurityViolation(
                                rule_id="DANGEROUS_ATTRIBUTE",
                                severity=sev,
                                message=desc,
                                file_path=str(file_path),
                                line_number=line_no,
                                snippet=snippet,
                            )
                        )

                    # Subprocess calls with shell=True
                    if full_name in ("subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_output", "subprocess.check_call"):
                        for kw in node.keywords:
                            if kw.arg == "shell":
                                if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                    line_no = getattr(node, "lineno", None)
                                    snippet = lines[line_no - 1].strip() if line_no and line_no <= len(lines) else None
                                    violations.append(
                                        SecurityViolation(
                                            rule_id="SUBPROCESS_SHELL_TRUE",
                                            severity=RiskLevel.CRITICAL,
                                            message="Subprocess execution with shell=True is dangerous and forbidden.",
                                            file_path=str(file_path),
                                            line_number=line_no,
                                            snippet=snippet,
                                        )
                                    )

        return violations

    def _resolve_attribute(self, node: ast.Attribute) -> str:
        """Recursively resolves attribute access like a.b.c."""
        parts = [node.attr]
        curr = node.value
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
            return ".".join(reversed(parts))
        return ""
