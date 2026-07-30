from typing import Dict, List, Optional

from app.tools.base import BaseTool


class ToolRegistry:
    """
    Stores all available tools and provides lookup by name.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool using its metadata.
        """
        self._tools[tool.metadata.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Retrieve a tool by its name.
        """
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """
        Return all registered tools.
        """
        return list(self._tools.values())


# Singleton registry
default_registry = ToolRegistry()