import uuid
import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.schemas.agent import AgentChatRequest, AgentChatResponse, AgentContext
from app.agent.orchestrator import AgentOrchestrator
from app.agent.planner import AgentPlanner
from app.gateway.proxy import AgentWAFProxy
from app.gateway.executor import ToolExecutor
from app.tools.registry import default_registry, ToolRegistry
from app.tools.search import SearchTool
from app.tools.file import FileTool
from app.tools.calculator import CalculatorTool
from app.core.config import settings

# Logging, WAF engine and DB elements
from app.policy.engine import PolicyEngine
from app.logging.repository import SQLiteAuditRepository
from app.logging.publisher import event_publisher
from app.logging.metrics import metrics_collector
from app.database.schema import init_banking_schema

# WAF Security Rules
from app.rules.rate_limit import RateLimitRule
from app.rules.parameter_validation import ParameterValidationRule
from app.rules.data_scope import DataScopeRule
from app.rules.sequence import SequenceRule
from app.core.policy_loader import policy_loader
from app.tools.banking import TransferMoneyTool, CheckBalanceTool, GetTransactionHistoryTool

router = APIRouter()

# Structured Logger
logger = logging.getLogger("agent_waf")

# Instantiating the SQLite Repository, seeding banking schema, and Policy Engine
audit_repo = SQLiteAuditRepository(settings.DATABASE_PATH)
init_banking_schema()
policy_engine = PolicyEngine()

def init_rules(engine: PolicyEngine) -> None:
    # Clear rules list to prevent duplicates on reload
    engine.rules = []
    
    # Reload policy data
    policy_loader.load()
    
    # Get config parameters
    rate_limit_cfg = policy_loader.get("rate_limit", {"max_calls": 5, "window_seconds": 60})
    param_validation_cfg = policy_loader.get("parameter_validation", {
        "max_param_size": 1000,
        "blocked_keywords": ["delete", "remove", "rm", "format", "drop database", "kill"]
    })
    sequence_cfg = policy_loader.get("sequence", {"dependencies": {"file_reader": ["search"]}})
    
    # Register rules in the exact order requested
    engine.register_rule(RateLimitRule(
        max_calls=rate_limit_cfg.get("max_calls", 5),
        window_seconds=rate_limit_cfg.get("window_seconds", 60)
    ))
    engine.register_rule(ParameterValidationRule(
        max_param_size=param_validation_cfg.get("max_param_size", 1000),
        blocked_keywords=param_validation_cfg.get("blocked_keywords")
    ))
    engine.register_rule(DataScopeRule())
    engine.register_rule(SequenceRule(
        dependencies=sequence_cfg.get("dependencies", {"file_reader": ["search"]})
    ))
    logger.info("WAF Rules initialized dynamically from policy file.")

# Initial Rules Registration
init_rules(policy_engine)

def get_registry() -> ToolRegistry:
    # Lazy register default tools if not already present
    if not default_registry.get_tool("search"):
        default_registry.register(SearchTool())
    if not default_registry.get_tool("file_reader"):
        default_registry.register(FileTool(sample_data_dir=settings.SAMPLE_DATA_DIR))
    if not default_registry.get_tool("calculator"):
        default_registry.register(CalculatorTool())
    if not default_registry.get_tool("transfer_money"):
        default_registry.register(TransferMoneyTool())
    if not default_registry.get_tool("check_balance"):
        default_registry.register(CheckBalanceTool())
    if not default_registry.get_tool("get_transaction_history"):
        default_registry.register(GetTransactionHistoryTool())
    return default_registry

def get_orchestrator(registry: ToolRegistry = Depends(get_registry)) -> AgentOrchestrator:
    planner = AgentPlanner(registry)
    tool_executor = ToolExecutor(registry)
    proxy = AgentWAFProxy(
        policy_engine=policy_engine,
        tool_executor=tool_executor,
        audit_repository=audit_repo,
        shadow_mode=settings.SHADOW_MODE
    )
    return AgentOrchestrator(planner, proxy)

@router.post("/agent/chat", response_model=AgentChatResponse)
async def chat(
    request: AgentChatRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> AgentChatResponse:
    """POST /agent/chat handles the chatbot conversation interaction loop."""
    request_id = str(uuid.uuid4())
    agent_id = request.agent_id or "default-agent"
    session_id = request.session_id or "default-session"
    user_id = request.user_id or "default-user"

    try:
        context = AgentContext(
            request_id=request_id,
            agent_id=agent_id,
            session_id=session_id,
            user_id=user_id,
            message=request.message
        )
        return orchestrator.run(context)
    except Exception as e:
        logger.error("Error in chat endpoint execution: %s", str(e))
        return AgentChatResponse(
            request_id=request_id,
            tool_used=None,
            response=f"WAF Execution Notice: {str(e)}",
            execution_time_ms=0.0
        )

@router.get("/metrics")
async def get_metrics():
    """GET /metrics aggregates fast in-memory statistics for the WAF dashboard."""
    return metrics_collector.get_metrics()

@router.get("/audit")
async def get_audit(limit: int = 50):
    """GET /audit lists recent audit log entries from the database."""
    logs = audit_repo.get_all(limit=limit)
    return [log.dict() for log in logs]

@router.get("/rules")
async def get_rules():
    """GET /rules displays names of registered WAF rules and settings."""
    return {
        "rules": [rule.__class__.__name__ for rule in policy_engine.rules],
        "total_rules": len(policy_engine.rules),
        "shadow_mode": settings.SHADOW_MODE
    }

@router.post("/rules/reload")
async def reload_rules():
    """POST /rules/reload triggers a reload of the rule engine registration."""
    init_rules(policy_engine)
    return {"status": "success", "message": "WAF rules successfully reloaded."}

@router.delete("/agent/logs/reset")
async def reset_logs():
    """DELETE /logs/reset deletes all audit logs and resets in-memory metrics."""
    try:
        audit_repo.clear_all()
        metrics_collector.reset()
        return {"status": "success", "message": "All WAF logs and metrics successfully reset."}
    except Exception as e:
        logger.error("Error resetting WAF logs: %s", str(e))
        return {"status": "error", "message": f"Failed to reset logs: {str(e)}"}

@router.websocket("/dashboard/ws")
async def websocket_endpoint(websocket: WebSocket):
    """GET /dashboard/ws manages active real-time dashboard WebSocket listeners."""
    await event_publisher.register(websocket)
    try:
        while True:
            # Wait for client keep-alives or handle disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_publisher.unregister(websocket)
    except Exception:
        event_publisher.unregister(websocket)
