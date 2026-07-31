from typing import Optional

from app.agent.planner import AgentPlanner
from app.gateway.proxy import AgentWAFProxy
from app.schemas.agent import AgentContext, AgentChatResponse
from app.schemas.tool import ToolInvocation
from app.utils.timing import execution_timer
from app.services.gemini import gemini_service


class AgentOrchestrator:
    def __init__(
        self,
        planner: AgentPlanner,
        proxy: AgentWAFProxy,
    ) -> None:
        self.planner = planner
        self.proxy = proxy

    def run(self, context: AgentContext) -> AgentChatResponse:
        """
        Agent execution flow:

        User
          ↓
        Planner (Gemini)
          ↓
        ToolInvocation
          ↓
        AgentWAFProxy (Deterministic + AI Risk checks)
          ↓
        Registry ➔ Tool ➔ Result
          ↓
        LLM final compilation ➔ Response to User
        """

        tool_used: Optional[str] = None
        is_blocked: bool = False
        rule_triggered: Optional[str] = None
        risk_score: Optional[str] = "LOW"
        waf_reason: Optional[str] = "Allowed by Agent WAF policy"

        with execution_timer() as timer:
            try:
                # Planner decides if it wants to invoke a tool, and returns a ToolInvocation
                invocation = self.planner.plan(context)

                if invocation:
                    tool_used = invocation.tool

                    # Convert planner output into standard ToolInvocation (ensures user_prompt carries over)
                    tool_request = ToolInvocation(
                        request_id=context.request_id,
                        agent_id=context.agent_id,
                        session_id=context.session_id,
                        tool=invocation.tool,
                        parameters=invocation.parameters,
                        user_prompt=context.message
                    )

                    # Route through proxy (interceptor layer)
                    tool_response = self.proxy.invoke(tool_request)

                    if tool_response.success:
                        # WAF allowed and tool executed successfully -> let LLM write final answer
                        response_text = gemini_service.generate_final_response(
                            prompt=context.message,
                            tool=invocation.tool,
                            params=invocation.parameters,
                            result=str(tool_response.result)
                        )
                        is_blocked = False
                        waf_reason = "Allowed by Agent WAF policy"
                        risk_score = "LOW"
                    else:
                        # WAF blocked or tool failed -> let LLM explain the block naturally
                        block_err = tool_response.error or "Tool execution failed."
                        response_text = gemini_service.explain_block(
                            prompt=context.message,
                            tool=invocation.tool,
                            reason=block_err
                        )
                        is_blocked = True
                        rule_triggered = getattr(tool_response, 'block_reason', None) or "SecurityPolicyViolation"
                        waf_reason = block_err
                        risk_score = "HIGH"
                else:
                    # No tool call was planned -> generate conversational natural response directly
                    response_text = gemini_service.generate_direct_response(context.message)

            except Exception as e:
                response_text = f"An unexpected error occurred during execution: {str(e)}"
                is_blocked = True
                waf_reason = str(e)

        return AgentChatResponse(
            request_id=context.request_id,
            tool_used=tool_used,
            response=response_text,
            execution_time_ms=timer.elapsed_ms,
            is_blocked=is_blocked,
            rule_triggered=rule_triggered,
            risk_score=risk_score,
            waf_reason=waf_reason,
        )