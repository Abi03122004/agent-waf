from typing import Any
from app.tools.registry import ToolRegistry
from app.schemas.tool import ToolInvocation, ToolResult
from app.utils.timing import execution_timer

class ToolExecutor:
    """
    Handles execution of registered tools. Separates execution logic
    (timeouts, registry lookups, errors, metrics) from WAF Proxy interception.
    """
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute(self, invocation: ToolInvocation) -> ToolResult:
        with execution_timer() as timer:
            tool = self.registry.get_tool(invocation.tool)
            if not tool:
                return ToolResult(
                    success=False,
                    tool=invocation.tool,
                    error=f"Tool '{invocation.tool}' is not registered in the system.",
                    execution_time_ms=timer.elapsed_ms
                )

            try:
                result = tool.execute(**invocation.parameters)
                return ToolResult(
                    success=True,
                    tool=invocation.tool,
                    result=result,
                    execution_time_ms=timer.elapsed_ms
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    tool=invocation.tool,
                    error=str(e),
                    execution_time_ms=timer.elapsed_ms
                )
