from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolMetadata(BaseModel):
    """
    Metadata describing a registered tool.
    """

    name: str = Field(
        ...,
        description="Unique tool name"
    )

    description: str = Field(
        ...,
        description="Description of the tool"
    )

    input_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="Expected input schema"
    )

    scopes: List[str] = Field(
        default_factory=list,
        description="Supported data scopes"
    )


class ToolInvocation(BaseModel):
    """
    Standard request object passed from the Planner
    to the Agent WAF Proxy.

    The Planner decides which tool to use.
    This object simply packages the request into
    a standard format for the WAF.
    """

    request_id: str = Field(
        ...,
        description="Unique request identifier"
    )

    agent_id: str = Field(
        ...,
        description="Unique agent identifier"
    )

    session_id: str = Field(
        ...,
        description="Current conversation/session identifier"
    )

    tool: str = Field(
        ...,
        description="Tool selected by the planner"
    )

    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters passed to the tool"
    )

    declared_scope: List[str] = Field(
        default_factory=list,
        description="Resources the agent is permitted to access"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Time when the tool invocation was created"
    )


class ToolResult(BaseModel):
    """
    Standard response returned by the Agent WAF Proxy.
    """

    success: bool = Field(
        ...,
        description="Whether tool execution succeeded"
    )

    blocked: bool = Field(
        default=False,
        description="Whether the request was blocked by the WAF"
    )

    tool: str = Field(
        ...,
        description="Tool that was requested"
    )

    result: Optional[Any] = Field(
        default=None,
        description="Tool execution result"
    )

    error: Optional[str] = Field(
        default=None,
        description="Execution error message"
    )

    block_reason: Optional[str] = Field(
        default=None,
        description="Reason the WAF blocked the request"
    )

    execution_time_ms: float = Field(
        default=0.0,
        description="Execution time in milliseconds"
    )


class RuleResult(BaseModel):
    """
    Result returned by an individual WAF rule.
    """

    allowed: bool = Field(
        ...,
        description="Whether the rule allows the request"
    )

    rule_name: str = Field(
        ...,
        description="Name of the rule that evaluated the request"
    )

    reason: str = Field(
        default="Allowed",
        description="Reason for allow/block decision"
    )


class AuditLogEntry(BaseModel):
    """
    Standard audit log entry for every intercepted tool call.
    This schema will be used in the Audit Logger phase.
    """

    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )

    request_id: str

    session_id: str

    agent_id: str

    tool: str

    sanitized_parameters: Dict[str, Any] = Field(
        default_factory=dict
    )

    allowed: bool

    blocked: bool

    rule_name: Optional[str] = None

    reason: Optional[str] = None

    execution_time_ms: float = 0.0