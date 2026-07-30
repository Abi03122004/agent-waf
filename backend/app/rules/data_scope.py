import os
from pathlib import Path
from typing import Tuple, Set
from app.rules.base import BaseRule
from app.schemas.tool import ToolInvocation

class DataScopeRule(BaseRule):
    """
    Restricts resource parameters (filename, path, filepath, resource) to reside inside the declared scope directory.
    """
    def __init__(self) -> None:
        self.resource_keys: Set[str] = {"filename", "path", "filepath", "resource"}

    def evaluate(self, invocation: ToolInvocation) -> Tuple[bool, str]:
        # Access the declared scope from invocation
        declared_scope = getattr(invocation, "declared_scope", None)
        if not declared_scope:
            return True, "Allowed"

        # Normalize declared_scope as a list of strings/paths
        scopes = [declared_scope] if isinstance(declared_scope, (str, Path)) else declared_scope

        # Resolve all scope directories
        scope_dirs = []
        for s in scopes:
            try:
                scope_dirs.append(Path(s).resolve())
            except Exception:
                pass

        if not scope_dirs:
            return True, "Allowed"

        # Iterate over parameters and validate only keys matching resource fields
        for key, val in invocation.parameters.items():
            if key.lower() in self.resource_keys and isinstance(val, str):
                try:
                    val_path = Path(val)
                    is_contained = False
                    
                    for scope_dir in scope_dirs:
                        target_path = val_path if val_path.is_absolute() else (scope_dir / val)
                        try:
                            resolved_target = target_path.resolve()
                            if resolved_target.is_relative_to(scope_dir):
                                is_contained = True
                                break
                        except Exception:
                            pass
                            
                    if not is_contained:
                        return (
                            False,
                            f"Access denied: Resource '{key}' is outside the declared scope {declared_scope}."
                        )
                except Exception as e:
                    return False, f"Invalid resource path parameter for '{key}': {str(e)}"

        return True, "Allowed"
