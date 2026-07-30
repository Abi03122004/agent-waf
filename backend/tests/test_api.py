import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "agent-waf"

def test_ready_endpoint():
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"

def test_agent_chat_search(capsys):
    payload = {
        "message": "Search Python tutorials"
    }
    response = client.post("/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["tool_used"] == "search"
    assert "Python is a high-level" in data["response"]
    assert data["execution_time_ms"] >= 0
    
    # Capture and verify proxy interception logging
    captured = capsys.readouterr()
    assert "[AgentWAF Proxy]" in captured.out
    assert "Tool: search" in captured.out
    assert '"query": "Python tutorials"' in captured.out

def test_agent_chat_file(capsys):
    payload = {
        "message": "read notes.txt"
    }
    response = client.post("/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["tool_used"] == "file_reader"
    assert "Welcome to Agent WAF" in data["response"]
    
    # Capture and verify proxy interception logging
    captured = capsys.readouterr()
    assert "[AgentWAF Proxy]" in captured.out
    assert "Tool: file_reader" in captured.out
    assert '"filename": "notes.txt"' in captured.out

def test_agent_chat_calculator(capsys):
    payload = {
        "message": "calculate 15 * 6"
    }
    response = client.post("/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["tool_used"] == "calculator"
    assert data["response"] == "90"
    
    # Capture and verify proxy interception logging
    captured = capsys.readouterr()
    assert "[AgentWAF Proxy]" in captured.out
    assert "Tool: calculator" in captured.out
    assert '"expression": "15 * 6"' in captured.out

def test_agent_chat_no_match(capsys):
    payload = {
        "message": "Write a poem about safety"
    }
    response = client.post("/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["tool_used"] is None
    assert "Planner could not match prompt" in data["response"]
    
    # Capouterr should be empty of WAF proxy interception because no tool was run
    captured = capsys.readouterr()
    assert "[AgentWAF Proxy]" not in captured.out
