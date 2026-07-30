import re
from typing import Tuple, Any
from app.rules.base import BaseRule
from app.schemas.tool import ToolInvocation

class ParameterValidationRule(BaseRule):
    """
    Validates parameters for security issues (SQLi, Prompt injection, path traversal, oversized fields).
    """
    def __init__(self, max_param_size: int = 1000) -> None:
        self.max_param_size = max_param_size
        
        # Substring/regex matching patterns for SQL Injection (case-insensitive)
        self.sqli_patterns = [
            r"(?i)\bdrop\s+table\b",
            r"(?i)\bdelete\s+from\b",
            r"(?i)\binsert\s+into\b",
            r"(?i)\bunion\s+select\b",
            r"(?i)\bor\s+1\s*=\s*1\b",
            r"--"
        ]
        
        # Substring/regex matching patterns for Prompt Injection (case-insensitive)
        self.prompt_inj_patterns = [
            r"(?i)\bignore\s+previous\s+instructions\b",
            r"(?i)\breveal\s+system\s+prompt\b",
            r"(?i)\bact\s+as\s+(?:a\s+)?developer\b",
            r"(?i)\bbypass\s+safety\b",
            r"(?i)\bforget\s+previous\s+instructions\b"
        ]

        # Substring/regex matching patterns for Destructive File Operations (case-insensitive)
        self.destructive_patterns = [
            r"(?i)\bdelete\s+(?:all\s+)?files?\b",
            r"(?i)\brm\s+-[a-z]*r[a-z]*\b",
            r"(?i)\bremove\s+(?:all\s+)?files?\b",
            r"(?i)\bformat\s+[a-z]:\b",
            r"(?i)\bkill\s+-9\b",
            r"(?i)\bdrop\s+database\b"
        ]

    def evaluate(self, invocation: ToolInvocation) -> Tuple[bool, str]:
        def validate_val(val: Any) -> Tuple[bool, str]:
            if isinstance(val, str):
                # 1. Path Traversal check
                # Check for relative directory escapes and known locations
                lower_val = val.lower()
                if "../../../" in val or "..\\" in val or "/etc/passwd" in lower_val or "c:\\windows" in lower_val:
                    return False, "Path Traversal attempt detected."

                # 2. SQL Injection check
                for pattern in self.sqli_patterns:
                    if re.search(pattern, val):
                        return False, "SQL Injection attempt detected."
                
                # 3. Prompt Injection check
                for pattern in self.prompt_inj_patterns:
                    if re.search(pattern, val):
                        return False, "Prompt Injection attempt detected."

                # 4. Destructive file operations check
                for pattern in self.destructive_patterns:
                    if re.search(pattern, val):
                        return False, "Destructive file command / malicious operation detected."

                # 5. Size constraint check
                if len(val) > self.max_param_size:
                    return False, f"Oversized input: parameter length {len(val)} exceeds max of {self.max_param_size}."
                        
            elif isinstance(val, dict):
                for k, v in val.items():
                    allowed, reason = validate_val(v)
                    if not allowed:
                        return False, f"Field '{k}' validation failed: {reason}"
            elif isinstance(val, list):
                for idx, item in enumerate(val):
                    allowed, reason = validate_val(item)
                    if not allowed:
                        return False, f"Index {idx} validation failed: {reason}"
            return True, "Allowed"

        return validate_val(invocation.parameters)
