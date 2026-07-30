from typing import Optional

from app.agent.planner import AgentPlanner
from app.gateway.proxy import AgentWAFProxy
from app.schemas.agent import AgentContext, AgentChatResponse
from app.schemas.tool import ToolInvocation
from app.utils.timing import execution_timer


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
        Planner
          ↓
        ToolInvocation
          ↓
        AgentWAFProxy
          ↓
        Registry
          ↓
        Tool
        """

        tool_used: Optional[str] = None
        response_text: str = ""

        with execution_timer() as timer:

            try:

                # Planner decides which tool to call
                invocation = self.planner.plan(context)

                if invocation:

                    tool_used = invocation.tool

                    # Convert planner output into a standard ToolInvocation
                    tool_request = ToolInvocation(
                        request_id=context.request_id,
                        agent_id=context.agent_id,
                        session_id=context.session_id,
                        tool=invocation.tool,
                        parameters=invocation.parameters,
                    )

                    # Every tool call MUST pass through the WAF Proxy
                    tool_response = self.proxy.invoke(tool_request)

                    if tool_response.success:
                        response_text = str(tool_response.result)
                    else:
                        response_text = (
                            tool_response.error
                            or "Tool execution failed."
                        )

                else:

                    response_text = (
                        f"Planner could not match prompt: '{context.message}' "
                        "to any available tools."
                    )

            except Exception as e:
                response_text = str(e)

        return AgentChatResponse(
            request_id=context.request_id,
            tool_used=tool_used,
            response=response_text,
            execution_time_ms=timer.elapsed_ms,
        )