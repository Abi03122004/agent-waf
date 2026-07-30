from collections import defaultdict
from typing import Tuple, List, Dict
from app.rules.base import BaseRule
from app.schemas.tool import ToolInvocation

class SequenceRule(BaseRule):
    """
    Enforces sequential call logic (e.g. file_reader must be preceded by search).
    Configurable tool dependency mapping.
    """
    def __init__(self, dependencies: Dict[str, List[str]] = None) -> None:
        self.dependencies = dependencies or {
            "file_reader": ["search"]
        }
        # session_id -> list of tools executed in order
        self.history: Dict[str, List[str]] = defaultdict(list)

    def evaluate(self, invocation: ToolInvocation) -> Tuple[bool, str]:
        session_id = invocation.session_id
        tool = invocation.tool

        # Verify dependency requirement
        if tool in self.dependencies:
            required_tools = self.dependencies[tool]
            session_history = self.history[session_id]
            
            if not any(req in session_history for req in required_tools):
                return (
                    False,
                    f"Sequence violation: Tool '{tool}' is not allowed without a preceding "
                    f"call to one of: {required_tools} in session '{session_id}'."
                )

        # Track history for session
        self.history[session_id].append(tool)
        return True, "Allowed"
