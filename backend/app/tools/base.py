from abc import ABC, abstractmethod
from typing import Any

from app.schemas.tool import ToolMetadata


class BaseTool(ABC):
    """
    Base class for every tool.

    Every concrete tool must:
    - expose metadata
    - implement execute()
    """

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """
        Metadata describing the tool.
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool.
        """
        pass