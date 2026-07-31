import re
from typing import Optional
from app.tools.registry import ToolRegistry
from app.schemas.agent import AgentContext
from app.schemas.tool import ToolInvocation
from app.services.gemini import gemini_service

class AgentPlanner:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def plan(self, context: AgentContext) -> Optional[ToolInvocation]:
        """
        Determine which tool to execute based on context message, registering the invocation parameters.
        Returns a ToolInvocation instance if a tool matches the user's intent.
        """
        message = context.message.strip()

        # 1. Search Tool Route
        # E.g. "search python", "Search fastapi", "search 'machine learning'"
        search_match = re.search(r'(?i)\bsearch\s+(.+)', message)
        if search_match:
            query = search_match.group(1).strip()
            # Clean up outer quotes
            query = re.sub(r'^["\']|["\']$', '', query)
            return ToolInvocation(
                request_id=context.request_id,
                agent_id=context.agent_id,
                session_id=context.session_id,
                tool="search",
                parameters={"query": query},
                user_prompt=message
            )

        # 2. File Tool Route
        # E.g. "read notes.txt", "read file notes.txt", "read 'data.json'"
        file_match = re.search(r'(?i)\bread\s+(?:file\s+)?([a-zA-Z0-9_\-\.\/]+)', message)
        if file_match:
            filename = file_match.group(1).strip()
            filename = re.sub(r'^["\']|["\']$', '', filename)
            return ToolInvocation(
                request_id=context.request_id,
                agent_id=context.agent_id,
                session_id=context.session_id,
                tool="file_reader",
                parameters={"filename": filename},
                user_prompt=message
            )

        # 3. Calculator Tool Route
        # E.g. "calculate 45+20", "calc 10 * 10", "math 2**8"
        calc_match = re.search(r'(?i)\b(?:calculate|calc|math)\s+(.+)', message)
        if calc_match:
            expression = calc_match.group(1).strip()
            return ToolInvocation(
                request_id=context.request_id,
                agent_id=context.agent_id,
                session_id=context.session_id,
                tool="calculator",
                parameters={"expression": expression},
                user_prompt=message
            )

        # Fallback Calculator Route (matches raw arithmetic calculations e.g. "45+20")
        if re.match(r'^[0-9\s\+\-\*\/\(\)\.\%\*]+$', message) and any(c in message for c in "+-*/%"):
            return ToolInvocation(
                request_id=context.request_id,
                agent_id=context.agent_id,
                session_id=context.session_id,
                tool="calculator",
                parameters={"expression": message},
                user_prompt=message
            )

        # 4. Destructive / Malicious Actions Route
        # E.g. "delete all file", "remove notes.txt", "rm -rf /"
        if any(w in message.lower() for w in ["delete", "remove", "rm", "format", "drop database", "kill"]):
            return ToolInvocation(
                request_id=context.request_id,
                agent_id=context.agent_id,
                session_id=context.session_id,
                tool="file_reader",
                parameters={"filename": message},
                user_prompt=message
            )

        # 5. AI Banking Route via Gemini (run only if local utility regexes did not match)
        banking_call = gemini_service.generate_banking_tool_call(message)
        tool_name = banking_call.get("tool")
        if tool_name and tool_name in ["transfer_money", "check_balance", "get_transaction_history"]:
            return ToolInvocation(
                request_id=context.request_id,
                agent_id=context.agent_id,
                session_id=context.session_id,
                tool=tool_name,
                parameters=banking_call.get("parameters", {}),
                user_prompt=message
            )

        return None
