from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Tuple
from app.rules.base import BaseRule
from app.schemas.tool import ToolInvocation

class RateLimiter(ABC):
    @abstractmethod
    def is_allowed(self, agent_id: str, tool_name: str) -> Tuple[bool, int, int]:
        """
        Check if request is allowed.
        Returns:
            (allowed: bool, current_calls: int, max_calls: int)
        """
        pass

class InMemoryRateLimiter(RateLimiter):
    def __init__(self, max_calls: int = 5, window_seconds: int = 60) -> None:
        self.max_calls = max_calls
        self.window = timedelta(seconds=window_seconds)
        # (agent_id, tool_name) -> deque of timestamps
        self.calls = defaultdict(deque)

    def is_allowed(self, agent_id: str, tool_name: str) -> Tuple[bool, int, int]:
        key = (agent_id, tool_name)
        now = datetime.utcnow()
        timestamps = self.calls[key]
        
        # Remove expired timestamps
        while timestamps and now - timestamps[0] > self.window:
            timestamps.popleft()
            
        if len(timestamps) >= self.max_calls:
            return False, len(timestamps), self.max_calls
            
        timestamps.append(now)
        return True, len(timestamps), self.max_calls

class RateLimitRule(BaseRule):
    """
    Limits tool calls per agent and tool using a decoupled RateLimiter interface.
    """
    def __init__(self, limiter: RateLimiter = None, max_calls: int = 5, window_seconds: int = 60) -> None:
        self.limiter = limiter or InMemoryRateLimiter(max_calls, window_seconds)

    def evaluate(self, invocation: ToolInvocation) -> Tuple[bool, str]:
        allowed, current, limit = self.limiter.is_allowed(invocation.agent_id, invocation.tool)
        if not allowed:
            return (
                False,
                f"Rate limit exceeded for tool '{invocation.tool}'. "
                f"Maximum {limit} calls permitted."
            )
        return True, "Allowed"