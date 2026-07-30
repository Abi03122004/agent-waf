import threading
import time
from collections import defaultdict, deque
from typing import Dict, Any

class MetricsCollector:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total_requests = 0
        self.allowed_requests = 0
        self.blocked_requests = 0
        
        # rule_name -> count of violations
        self.rule_violations = defaultdict(int)
        
        # Timestamps for calculating rolling RPM
        self.request_timestamps = deque()

    def record_request(self, allowed: bool, blocked: bool, rule_triggered: str = None) -> None:
        """Increment counters in a thread-safe manner."""
        with self._lock:
            self.total_requests += 1
            if allowed:
                self.allowed_requests += 1
            if blocked:
                self.blocked_requests += 1
            if rule_triggered:
                self.rule_violations[rule_triggered] += 1
            
            self.request_timestamps.append(time.time())

    def get_metrics(self) -> Dict[str, Any]:
        """Aggregate fast in-memory stats without querying SQLite database."""
        with self._lock:
            now = time.time()
            # Remove timestamps older than 60 seconds
            while self.request_timestamps and now - self.request_timestamps[0] > 60:
                self.request_timestamps.popleft()
            
            rpm = len(self.request_timestamps)
            
            # Find the most triggered rule
            most_triggered_rule = None
            if self.rule_violations:
                most_triggered_rule = max(self.rule_violations, key=self.rule_violations.get)
            
            return {
                "total_requests": self.total_requests,
                "allowed_requests": self.allowed_requests,
                "blocked_requests": self.blocked_requests,
                "requests_per_minute": rpm,
                "rule_violations": dict(self.rule_violations),
                "most_triggered_rule": most_triggered_rule
            }

# Create a singleton global metrics collector
metrics_collector = MetricsCollector()
