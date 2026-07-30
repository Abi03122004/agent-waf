from abc import ABC, abstractmethod
from typing import Tuple

from app.schemas.tool import ToolInvocation


class BaseRule(ABC):
    """
    Base class for every Agent WAF security rule.
    """

    @abstractmethod
    def evaluate(
        self,
        invocation: ToolInvocation,
    ) -> Tuple[bool, str]:
        """
        Evaluate a ToolInvocation.

        Returns:
            (allowed, reason)
        """
        pass