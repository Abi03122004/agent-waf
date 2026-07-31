from pydantic import BaseModel, Field
from typing import Optional

class AgentContext(BaseModel):
    request_id: str = Field(description="Unique UUID generated for each API request to track standard object flow")
    agent_id: str = Field(default="default-agent", description="Identifier for the agent instance")
    session_id: str = Field(default="default-session", description="Session identifier for tracking sequences")
    user_id: str = Field(default="default-user", description="Identifier for the end-user")
    message: str = Field(description="The user prompt or query")

class AgentChatRequest(BaseModel):
    message: str = Field(description="User input prompt or command for the agent to execute")
    agent_id: Optional[str] = Field(default="default-agent", description="Optional agent identifier")
    session_id: Optional[str] = Field(default="default-session", description="Optional session tracking identifier")
    user_id: Optional[str] = Field(default="default-user", description="Optional user tracking identifier")

class AgentChatResponse(BaseModel):
    request_id: str = Field(description="The UUID corresponding to the request context")
    tool_used: Optional[str] = Field(default=None, description="The name of the tool executed, or null if no tool was run")
    response: str = Field(description="Text output result from the agent/tool execution")
    execution_time_ms: float = Field(description="Total time taken to execute request in milliseconds")
    is_blocked: bool = Field(default=False, description="Whether the request was intercepted and blocked by WAF")
    rule_triggered: Optional[str] = Field(default=None, description="Name of the security rule triggered if blocked")
    risk_score: Optional[str] = Field(default="LOW", description="AI Security risk classification score")
    waf_reason: Optional[str] = Field(default=None, description="Human-readable WAF decision explanation")
