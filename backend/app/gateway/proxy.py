import logging
import asyncio
from datetime import datetime
from typing import Optional

from app.schemas.tool import ToolInvocation, ToolResult
from app.policy.engine import PolicyEngine
from app.gateway.executor import ToolExecutor
from app.logging.repository import AuditRepository, AuditLogEntry
from app.logging.publisher import event_publisher
from app.logging.metrics import metrics_collector

# Configure structured logging
logger = logging.getLogger("agent_waf")

class AgentWAFProxy:
    """
    Transparent proxy between the AI Agent and the ToolExecutor.
    Evaluates security policies, logs requests, tracks metrics,
    broadcasts WebSocket events, and executes tools.
    """
    def __init__(
        self,
        policy_engine: PolicyEngine,
        tool_executor: ToolExecutor,
        audit_repository: AuditRepository,
        shadow_mode: bool = False
    ) -> None:
        self.policy_engine = policy_engine
        self.tool_executor = tool_executor
        self.audit_repository = audit_repository
        self.shadow_mode = shadow_mode

    def invoke(self, invocation: ToolInvocation) -> ToolResult:
        # Structured log interception
        logger.info(
            "WAF Intercepted tool call: RequestID=%s, Agent=%s, Tool=%s, Session=%s",
            invocation.request_id, invocation.agent_id, invocation.tool, invocation.session_id
        )
        import json
        print(f"[AgentWAF Proxy] Intercepted tool call. Tool: {invocation.tool}, Parameters: {json.dumps(invocation.parameters)}")

        # 1. Evaluate rules
        allowed, reason, rule_triggered = self.policy_engine.evaluate(invocation)

        blocked = not allowed and not self.shadow_mode
        would_block = not allowed and self.shadow_mode

        # 2. Block execution (unless in shadow mode)
        if blocked:
            logger.warning(
                "WAF Blocked Execution: RequestID=%s, Tool=%s, Rule=%s, Reason=%s",
                invocation.request_id, invocation.tool, rule_triggered, reason
            )

            result = ToolResult(
                success=False,
                tool=invocation.tool,
                error=reason,
                execution_time_ms=0.0,
                blocked=True,
                block_reason=reason
            )

            # Log audit details
            entry = AuditLogEntry(
                timestamp=datetime.utcnow().isoformat(),
                request_id=invocation.request_id,
                session_id=invocation.session_id,
                agent_id=invocation.agent_id,
                tool=invocation.tool,
                parameters=invocation.parameters,
                allowed=False,
                blocked=True,
                would_block=False,
                rule_triggered=rule_triggered,
                reason=reason,
                execution_time_ms=0.0
            )
            self.audit_repository.save(entry)

            # Record in fast in-memory metrics collector
            metrics_collector.record_request(
                allowed=False,
                blocked=True,
                rule_triggered=rule_triggered
            )

            # Asynchronously broadcast event to WebSocket clients
            self._async_broadcast(entry)

            return result

        # 3. Allow execution (approved or shadowed)
        logger.info(
            "WAF Allowed Execution: RequestID=%s, Tool=%s (ShadowMode=%s)",
            invocation.request_id, invocation.tool, self.shadow_mode
        )

        tool_result = self.tool_executor.execute(invocation)

        # Save audit logs
        entry = AuditLogEntry(
            timestamp=datetime.utcnow().isoformat(),
            request_id=invocation.request_id,
            session_id=invocation.session_id,
            agent_id=invocation.agent_id,
            tool=invocation.tool,
            parameters=invocation.parameters,
            allowed=True,
            blocked=False,
            would_block=would_block,
            rule_triggered=rule_triggered if not allowed else None,
            reason=reason if not allowed else None,
            execution_time_ms=tool_result.execution_time_ms
        )
        self.audit_repository.save(entry)

        # Update metrics collector
        metrics_collector.record_request(
            allowed=True,
            blocked=False,
            rule_triggered=rule_triggered if not allowed else None
        )

        # Broadcast event
        self._async_broadcast(entry)

        return tool_result

    def _async_broadcast(self, entry: AuditLogEntry) -> None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(event_publisher.publish(entry.dict()))
        except Exception:
            pass