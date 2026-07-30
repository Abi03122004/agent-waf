import pytest
from pathlib import Path
from app.tools.registry import ToolRegistry
from app.tools.search import SearchTool
from app.tools.file import FileTool
from app.tools.calculator import CalculatorTool
from app.agent.planner import AgentPlanner
from app.schemas.agent import AgentContext

def test_tool_registry():
    registry = ToolRegistry()
    search_tool = SearchTool()
    registry.register(search_tool)
    
    assert registry.get_tool("search") == search_tool
    assert registry.get_tool("nonexistent") is None
    assert search_tool in registry.list_tools()

def test_search_tool():
    tool = SearchTool()
    
    # Check metadata
    meta = tool.metadata
    assert meta.name == "search"
    assert "query" in meta.input_schema["properties"]
    
    # Test valid searches
    res_python = tool.execute(query="Tell me about python")
    assert "Python is a high-level" in res_python
    
    res_fastapi = tool.execute(query="FastAPI docs")
    assert "FastAPI is a modern" in res_fastapi

    # Test fallback search
    res_fallback = tool.execute(query="golang coding")
    assert "No specific matches found" in res_fallback

def test_file_tool(tmp_path):
    # Set up sandbox directory
    sample_dir = tmp_path / "sample_data"
    sample_dir.mkdir()
    
    # Create test files
    valid_file = sample_dir / "notes.txt"
    valid_file.write_text("Hello, file reader!", encoding="utf-8")
    
    # Create file outside
    outside_file = tmp_path / "passwd.txt"
    outside_file.write_text("root:x:0:0", encoding="utf-8")
    
    tool = FileTool(sample_data_dir=sample_dir)
    
    # Test read valid file
    res = tool.execute(filename="notes.txt")
    assert res == "Hello, file reader!"
    
    # Test file not found inside safe dir
    with pytest.raises(FileNotFoundError):
        tool.execute(filename="nonexistent.txt")
        
    # Test path traversal prevention
    with pytest.raises(PermissionError):
        tool.execute(filename="../passwd.txt")

    with pytest.raises(PermissionError):
        tool.execute(filename="../../passwd.txt")

def test_calculator_tool():
    tool = CalculatorTool()
    
    # Test basic evaluations
    assert tool.execute(expression="45 + 20") == "65"
    assert tool.execute(expression="100 - 5 * 10") == "50"
    assert tool.execute(expression="(2 + 3) * 5") == "25"
    assert tool.execute(expression="-10 + 4.5") == "-5.5"
    assert tool.execute(expression="2 ** 6") == "64"
    assert tool.execute(expression="10 % 3") == "1"

    # Test division by zero safety
    with pytest.raises(ValueError) as excinfo:
        tool.execute(expression="50 / 0")
    assert "Division by zero" in str(excinfo.value)

    # Test AST parsing safety restrictions
    with pytest.raises(ValueError) as excinfo:
        tool.execute(expression="__import__('os').system('clear')")
    assert "Failed to evaluate expression" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        tool.execute(expression="[x for x in [1, 2]]")
    assert "Failed to evaluate expression" in str(excinfo.value)

    # Test power operation resource protection limits
    with pytest.raises(ValueError) as excinfo:
        tool.execute(expression="999 ** 200")
    assert "Power operation parameters exceed safety limits" in str(excinfo.value)

def test_agent_planner():
    registry = ToolRegistry()
    registry.register(SearchTool())
    registry.register(FileTool(sample_data_dir=Path("sample_data")))
    registry.register(CalculatorTool())
    
    planner = AgentPlanner(registry)
    
    # 1. Search trigger
    ctx_search = AgentContext(
        request_id="req-1",
        agent_id="test",
        session_id="sess-1",
        user_id="user-1",
        message="Search Python tutorials"
    )
    inv_search = planner.plan(ctx_search)
    assert inv_search is not None
    assert inv_search.tool == "search"
    assert inv_search.parameters == {"query": "Python tutorials"}

    # 2. File trigger
    ctx_file = AgentContext(
        request_id="req-2",
        agent_id="test",
        session_id="sess-1",
        user_id="user-1",
        message="read notes.txt"
    )
    inv_file = planner.plan(ctx_file)
    assert inv_file is not None
    assert inv_file.tool == "file_reader"
    assert inv_file.parameters == {"filename": "notes.txt"}

    # 3. Calculator triggers
    ctx_calc = AgentContext(
        request_id="req-3",
        agent_id="test",
        session_id="sess-1",
        user_id="user-1",
        message="Calculate 45+20"
    )
    inv_calc = planner.plan(ctx_calc)
    assert inv_calc is not None
    assert inv_calc.tool == "calculator"
    assert inv_calc.parameters == {"expression": "45+20"}

    # Raw math expression trigger
    ctx_math = AgentContext(
        request_id="req-4",
        agent_id="test",
        session_id="sess-1",
        user_id="user-1",
        message="12 * 12"
    )
    inv_math = planner.plan(ctx_math)
    assert inv_math is not None
    assert inv_math.tool == "calculator"
    assert inv_math.parameters == {"expression": "12 * 12"}

    # No match
    ctx_none = AgentContext(
        request_id="req-5",
        agent_id="test",
        session_id="sess-1",
        user_id="user-1",
        message="Hello agent, how are you today?"
    )
    assert planner.plan(ctx_none) is None
