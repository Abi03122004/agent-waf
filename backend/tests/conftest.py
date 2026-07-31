import pytest
import re
from unittest.mock import MagicMock
from app.services.gemini import GeminiService

@pytest.fixture(autouse=True)
def mock_gemini_service(monkeypatch):
    """
    Automatically mock all external Gemini API calls during backend testing.
    This prevents hitting the 5-requests-per-minute API rate limits
    and aligns outputs with existing test assertion requirements.
    """
    def mock_generate_banking_tool_call(self, prompt: str):
        # Mirror the planning behavior for tests
        message = prompt.strip()
        
        search_match = re.search(r'(?i)\bsearch\s+(.+)', message)
        if search_match:
            query = re.sub(r'^["\']|["\']$', '', search_match.group(1).strip())
            return {"tool": "search", "parameters": {"query": query}}
            
        file_match = re.search(r'(?i)\bread\s+(?:file\s+)?([a-zA-Z0-9_\-\.\/]+)', message)
        if file_match:
            filename = re.sub(r'^["\']|["\']$', '', file_match.group(1).strip())
            return {"tool": "file_reader", "parameters": {"filename": filename}}
            
        calc_match = re.search(r'(?i)\b(?:calculate|calc|math)\s+(.+)', message)
        if calc_match:
            expression = calc_match.group(1).strip()
            return {"tool": "calculator", "parameters": {"expression": expression}}
            
        if re.match(r'^[0-9\s\+\-\*\/\(\)\.\%\*]+$', message) and any(c in message for c in "+-*/%"):
            return {"tool": "calculator", "parameters": {"expression": message}}

        if any(w in message.lower() for w in ["delete", "remove", "rm", "format", "drop database", "kill"]):
            return {"tool": "file_reader", "parameters": {"filename": message}}
            
        return {"tool": "none", "parameters": {}}

    def mock_classify_security_risk(self, prompt: str, tool: str, params: dict, policy: dict, session_history: list = None):
        # Match injection signatures in parameters to simulate security classifier triggers
        param_str = str(params).lower()
        if any(w in param_str for w in ["drop table", "union select", "ignore previous instructions", "../", "..\\"]):
            return {"risk": "HIGH", "decision": "BLOCK", "reason": "AI Security Classifier detected injection."}
        return {"risk": "LOW", "decision": "ALLOW", "reason": "Mocked allow."}

    def mock_generate_direct_response(self, prompt: str):
        return f"Planner could not match prompt: '{prompt}' to any available tools."

    def mock_explain_block(self, prompt: str, tool: str, reason: str):
        return reason

    def mock_generate_final_response(self, prompt: str, tool: str, params: dict, result: str):
        return result

    # Apply monkeypatching to mock methods on the GeminiService class
    monkeypatch.setattr(GeminiService, "generate_banking_tool_call", mock_generate_banking_tool_call)
    monkeypatch.setattr(GeminiService, "classify_security_risk", mock_classify_security_risk)
    monkeypatch.setattr(GeminiService, "generate_direct_response", mock_generate_direct_response)
    monkeypatch.setattr(GeminiService, "explain_block", mock_explain_block)
    monkeypatch.setattr(GeminiService, "generate_final_response", mock_generate_final_response)
