from typing import Any
from app.tools.base import BaseTool
from app.schemas.tool import ToolMetadata

class SearchTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="search",
            description="Simulated web search tool. Searches articles, tutorials, and documentations.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query term"
                    }
                },
                "required": ["query"]
            },
            version="1.0.0",
            allowed_scope="web_search"
        )

    def execute(self, query: str, **kwargs: Any) -> str:
        query_lower = query.lower()
        
        # Simple simulated database
        database = {
            "python": (
                "Python is a high-level, general-purpose programming language. "
                "Tutorials can be found on realpython.com and docs.python.org."
            ),
            "fastapi": (
                "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ "
                "based on standard Python type hints. Official docs: https://fastapi.tiangolo.com/"
            ),
            "waf": (
                "A Web Application Firewall (WAF) helps protect web applications by filtering and monitoring HTTP traffic "
                "between a web application and the Internet."
            )
        }
        
        for key, value in database.items():
            if key in query_lower:
                return f"Search results for '{query}': {value}"
                
        return f"Search results for '{query}': No specific matches found. Try searching for 'python' or 'fastapi'."
