from typing import List, Tuple, Optional

from app.schemas.tool import ToolInvocation


class PolicyEngine:
    """
    Central policy evaluator.

    Every tool invocation is evaluated here before
    reaching the Tool Registry.
    """

    def __init__(self):
        self.rules = []

    def register_rule(self, rule):
        """
        Register a security rule.
        """
        self.rules.append(rule)

    def evaluate(
        self,
        invocation: ToolInvocation
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Evaluate all registered rules sequentially.

        Returns:
            (allowed, reason, triggered_rule)
        """
        for rule in self.rules:
            allowed, reason = rule.evaluate(invocation)
            if not allowed:
                return False, reason, rule.__class__.__name__

        return True, "Allowed", None