"""
SHIVANI Secret Scanner & Pre-Indexing Redaction Engine
Ensures zero-secret ingestion into search indices and LLM contexts.
Scans for credentials, tokens, private keys, connection strings, and prompt injections.
"""

import math
import re
from typing import Any, Dict, List, Pattern, Tuple


class SecretScanner:
    """Pre-indexing security scanner that intercepts and redacts sensitive credentials."""

    SECRET_PATTERNS: List[Tuple[str, Pattern[str]]] = [
        ("OPENAI_KEY", re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE)),
        ("GITHUB_PAT", re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,}", re.IGNORECASE)),
        ("GITHUB_FINE_GRAINED", re.compile(r"github_pat_[a-zA-Z0-9_]{40,}", re.IGNORECASE)),
        ("AWS_ACCESS_KEY", re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}")),
        ("SLACK_TOKEN", re.compile(r"xox[baprs]-[0-9a-zA-Z-]{10,}", re.IGNORECASE)),
        ("PRIVATE_KEY", re.compile(r"-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH)?\s*PRIVATE KEY-----[\s\S]*?-----END\s+(?:RSA|DSA|EC|OPENSSH)?\s*PRIVATE KEY-----")),
        ("DB_CONNECTION_STRING", re.compile(r"(?:postgres|postgresql|mysql|mongodb(?:\+srv)?|redis|amqp):\/\/[^:\s]+:([^@\s]+)@[^\s\/]+", re.IGNORECASE)),
        ("GENERIC_BEARER", re.compile(r"(?:bearer\s+)([a-zA-Z0-9_\-\.]{25,})", re.IGNORECASE)),
        ("ENV_SECRET_ASSIGNMENT", re.compile(r"(?:password|passwd|secret|api_key|token|auth_token|client_secret|private_key)\s*[:=]\s*[\"']?(?!\[REDACTED_)([^\"'\s\[]{8,})[\"']?", re.IGNORECASE)),
    ]

    INJECTION_PATTERNS: List[Pattern[str]] = [
        re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?", re.IGNORECASE),
        re.compile(r"disregard\s+(?:all\s+)?(?:previous|prior)\s+(?:rules|instructions?|prompts?)", re.IGNORECASE),
        re.compile(r"system\s*override\s*:\s*you\s+are\s+now", re.IGNORECASE),
        re.compile(r"<\s*\|?\s*im_start\s*\|?\s*>", re.IGNORECASE),
        re.compile(r"<\s*\|?\s*im_end\s*\|?\s*>", re.IGNORECASE),
    ]

    @classmethod
    def calculate_shannon_entropy(cls, text: str) -> float:
        """Calculates Shannon entropy to detect high-entropy random keys."""
        if not text:
            return 0.0
        entropy = 0.0
        length = len(text)
        counts: Dict[str, int] = {}
        for c in text:
            counts[c] = counts.get(c, 0) + 1
        for count in counts.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    @classmethod
    def scan_for_secrets(cls, text: str) -> List[Dict[str, Any]]:
        """Scans text and returns list of detected secrets and locations."""
        findings: List[Dict[str, Any]] = []
        for name, pattern in cls.SECRET_PATTERNS:
            for match in pattern.finditer(text):
                matched_str = match.group(0)
                findings.append({
                    "type": name,
                    "span": match.span(),
                    "matched_sample": matched_str[:4] + "..." + matched_str[-4:] if len(matched_str) > 8 else "***",
                })
        return findings

    @classmethod
    def redact_secrets(cls, text: str) -> str:
        """Redacts all detected secrets with standard security masks."""
        redacted = text
        for name, pattern in cls.SECRET_PATTERNS:
            if name == "DB_CONNECTION_STRING":
                # Redact only the password segment inside connection URI
                def _mask_db_pass(m: re.Match) -> str:
                    full = m.group(0)
                    pwd = m.group(1)
                    return full.replace(f":{pwd}@", ":[REDACTED_PASSWORD]@")
                redacted = pattern.sub(_mask_db_pass, redacted)
            elif name == "ENV_SECRET_ASSIGNMENT":
                def _mask_env_val(m: re.Match) -> str:
                    full = m.group(0)
                    val = m.group(1)
                    return full.replace(val, "[REDACTED_SECRET]")
                redacted = pattern.sub(_mask_env_val, redacted)
            elif name == "GENERIC_BEARER":
                def _mask_bearer(m: re.Match) -> str:
                    token = m.group(1)
                    return m.group(0).replace(token, "[REDACTED_TOKEN]")
                redacted = pattern.sub(_mask_bearer, redacted)
            else:
                redacted = pattern.sub(f"[REDACTED_{name}]", redacted)
        return redacted

    @classmethod
    def sanitize_prompt_injections(cls, text: str) -> str:
        """Neutralizes embedded prompt injections from external documents."""
        sanitized = text
        for pattern in cls.INJECTION_PATTERNS:
            sanitized = pattern.sub("[SAFETY_NEUTRALIZED_PROMPT_INJECTION]", sanitized)
        return sanitized

    @classmethod
    def clean_document(cls, text: str) -> str:
        """Complete pre-indexing sanitizer: redacts secrets and neutralizes prompt injections."""
        text = cls.redact_secrets(text)
        text = cls.sanitize_prompt_injections(text)
        return text
