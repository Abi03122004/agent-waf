import os
from pathlib import Path
from typing import Any
from app.tools.base import BaseTool
from app.schemas.tool import ToolMetadata

class FileTool(BaseTool):
    def __init__(self, sample_data_dir: Path) -> None:
        # Resolve the root directory for validation
        self.sample_data_dir = sample_data_dir.resolve()

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_reader",
            description="Reads the text content of a file from the safe sample_data directory.",
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the file to read (must reside inside the sample_data directory)"
                    }
                },
                "required": ["filename"]
            },
            version="1.0.0",
            allowed_scope="local_file_read"
        )

    def execute(self, filename: str, **kwargs: Any) -> str:
        # Prevent traversal outside allowed directory bounds
        target_path = (self.sample_data_dir / filename).resolve()
        
        if not target_path.is_relative_to(self.sample_data_dir):
            raise PermissionError("Access denied: File access is restricted to the sample_data directory.")
            
        if not target_path.exists():
            raise FileNotFoundError(f"File '{filename}' does not exist.")
            
        if not target_path.is_file():
            raise ValueError(f"'{filename}' is not a file.")
            
        return target_path.read_text(encoding="utf-8")
