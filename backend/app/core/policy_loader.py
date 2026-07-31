import json
import os
from typing import Dict, Any

class PolicyLoader:
    def __init__(self, policy_path: str) -> None:
        self.policy_path = policy_path
        self.policy_data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.policy_path):
            try:
                with open(self.policy_path, "r", encoding="utf-8") as f:
                    self.policy_data = json.load(f)
            except Exception as e:
                import logging
                logging.getLogger("agent_waf").error("Failed to load policy file: %s", str(e))
                self.policy_data = {}
        else:
            self.policy_data = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.policy_data.get(key, default)

# Resolve policy path relative to this core package
POLICY_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "policy.json")
policy_loader = PolicyLoader(POLICY_FILE_PATH)
