import logging
import asyncio
import json
from datetime import datetime
from typing import Optional

from app.schemas.tool import ToolInvocation, ToolResult
from app.policy.engine import PolicyEngine
from app.gateway.executor import ToolExecutor
from app.logging.repository import AuditRepository, AuditLogEntry
from app.logging.publisher import event_publisher
from app.logging.metrics import metrics_collector
from app.services.gemini import gemini_service
from app.core.policy_loader import policy_loader

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
        print(f"[AgentWAF Proxy] Intercepted tool call. Tool: {invocation.tool}, Parameters: {json.dumps(invocation.parameters)}")

        # --- Tier 1: Deterministic Rules ---
        det_allowed, det_reason, det_rule = self.policy_engine.evaluate(invocation)

        if not det_allowed:
            blocked = not self.shadow_mode
            would_block = self.shadow_mode
            reason = f"Deterministic WAF block ({det_rule}): {det_reason}"
            
            logger.warning(
                "WAF Intercept (Deterministic): RequestID=%s, Tool=%s, Rule=%s, Reason=%s, Blocked=%s",
                invocation.request_id, invocation.tool, det_rule, det_reason, blocked
            )

            if blocked:
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
                    rule_triggered=det_rule,
                    reason=reason,
                    execution_time_ms=0.0,
                    user_prompt=invocation.user_prompt,
                    rule_result=json.dumps({"status": "BLOCK", "rule": det_rule, "reason": det_reason}),
                    ai_risk_score="LOW",
                    ai_reason="Bypassed due to deterministic rule block.",
                    final_decision="BLOCK"
                )
                self._save_and_log_audit(entry)

                # Record in metrics collector
                metrics_collector.record_request(
                    allowed=False,
                    blocked=True,
                    rule_triggered=det_rule
                )

                # Asynchronously broadcast event to WebSocket clients
                self._async_broadcast(entry)

                return result
            else:
                # In shadow mode, run the tool instead!
                logger.info(
                    "WAF Allowed Execution (Deterministic ShadowMode): RequestID=%s, Tool=%s",
                    invocation.request_id, invocation.tool
                )
                tool_result = self.tool_executor.execute(invocation)

                entry = AuditLogEntry(
                    timestamp=datetime.utcnow().isoformat(),
                    request_id=invocation.request_id,
                    session_id=invocation.session_id,
                    agent_id=invocation.agent_id,
                    tool=invocation.tool,
                    parameters=invocation.parameters,
                    allowed=True,
                    blocked=False,
                    would_block=True,
                    rule_triggered=det_rule,
                    reason=reason,
                    execution_time_ms=tool_result.execution_time_ms,
                    user_prompt=invocation.user_prompt,
                    rule_result=json.dumps({"status": "BLOCK", "rule": det_rule, "reason": det_reason}),
                    ai_risk_score="LOW",
                    ai_reason="Bypassed due to deterministic rule block (Shadow Mode).",
                    final_decision="SHADOW_BLOCK"
                )
                self._save_and_log_audit(entry)

                metrics_collector.record_request(
                    allowed=True,
                    blocked=False,
                    rule_triggered=det_rule
                )
                self._async_broadcast(entry)
                return tool_result

        # --- Tier 2: AI Security Classifier ---
        logger.info("Deterministic rules passed. Triggering AI Security Classifier...")
        
        # Resolve session history from SequenceRule if registered
        session_history = []
        for rule in self.policy_engine.rules:
            if rule.__class__.__name__ == "SequenceRule" and hasattr(rule, "history"):
                session_history = rule.history.get(invocation.session_id, [])

        ai_res = gemini_service.classify_security_risk(
            prompt=invocation.user_prompt or "",
            tool=invocation.tool,
            params=invocation.parameters,
            policy=policy_loader.policy_data,
            session_history=session_history
        )

        ai_risk = ai_res.get("risk", "LOW")
        ai_decision = ai_res.get("decision", "ALLOW")
        ai_reason = ai_res.get("reason", "No security risk detected.")

        ai_blocked = (ai_decision == "BLOCK")
        
        # Decide if this results in WAF block (taking shadow mode into account)
        blocked = ai_blocked and not self.shadow_mode
        would_block = ai_blocked and self.shadow_mode
        allowed = not blocked

        reason = f"AI WAF {ai_decision} (Risk: {ai_risk}): {ai_reason}"

        if blocked:
            logger.warning(
                "WAF Blocked Execution (AI Classifier): RequestID=%s, Tool=%s, Risk=%s, Reason=%s",
                invocation.request_id, invocation.tool, ai_risk, ai_reason
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
                rule_triggered="AI_Classifier",
                reason=reason,
                execution_time_ms=0.0,
                user_prompt=invocation.user_prompt,
                rule_result=json.dumps({"status": "ALLOW", "reason": "All deterministic rules passed."}),
                ai_risk_score=ai_risk,
                ai_reason=ai_reason,
                final_decision=ai_decision
            )
            self._save_and_log_audit(entry)

            # Record in metrics
            metrics_collector.record_request(
                allowed=False,
                blocked=True,
                rule_triggered="AI_Classifier"
            )

            self._async_broadcast(entry)
            return result

        # --- Allowed Execution (Deterministic passed, AI either allowed or shadow blocked) ---
        logger.info(
            "WAF Allowed Execution: RequestID=%s, Tool=%s (ShadowMode=%s, AI Decision=%s)",
            invocation.request_id, invocation.tool, self.shadow_mode, ai_decision
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
            rule_triggered="AI_Classifier" if would_block else None,
            reason=reason if would_block else None,
            execution_time_ms=tool_result.execution_time_ms,
            user_prompt=invocation.user_prompt,
            rule_result=json.dumps({"status": "ALLOW", "reason": "All deterministic rules passed."}),
            ai_risk_score=ai_risk,
            ai_reason=ai_reason,
            final_decision=ai_decision if not would_block else "BLOCK"
        )
        self._save_and_log_audit(entry)

        # Update metrics collector
        metrics_collector.record_request(
            allowed=True,
            blocked=False,
            rule_triggered="AI_Classifier" if would_block else None
        )

        # Broadcast event
        self._async_broadcast(entry)

        return tool_result

    def _async_broadcast(self, entry: AuditLogEntry) -> None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Serialize properly using dict
                loop.create_task(event_publisher.publish(entry.dict()))
        except Exception:
            pass

    def _save_and_log_audit(self, entry: AuditLogEntry) -> None:
        # Save to database repository
        self.audit_repository.save(entry)
        
        # Emit structured JSON audit log to stdout/stderr
        audit_dict = {
            "timestamp": entry.timestamp,
            "request_id": entry.request_id,
            "agent_id": entry.agent_id,
            "session_id": entry.session_id,
            "tool": entry.tool,
            "decision": "blocked" if entry.blocked else "allowed",
            "would_block": entry.would_block,
            "rule_triggered": entry.rule_triggered,
            "reason": entry.reason,
            "execution_time_ms": entry.execution_time_ms,
            "ai_risk_score": entry.ai_risk_score,
            "final_decision": entry.final_decision
        }
        logger.info(json.dumps(audit_dict))