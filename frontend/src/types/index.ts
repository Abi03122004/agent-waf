export interface AgentChatRequest {
  message: string;
  agent_id?: string;
  session_id?: string;
}

export interface AgentChatResponse {
  request_id: string;
  tool_used?: string | null;
  response: string;
  execution_time_ms: number;
}

export interface AuditLogEntry {
  timestamp: string;
  request_id: string;
  session_id: string;
  agent_id: string;
  tool: string;
  parameters: Record<string, any>;
  allowed: boolean;
  blocked: boolean;
  would_block: boolean;
  rule_triggered?: string | null;
  reason?: string | null;
  execution_time_ms: number;
}

export interface MetricsData {
  total_requests: number;
  allowed_requests: number;
  blocked_requests: number;
  requests_per_minute: number;
  rule_violations: Record<string, number>;
  most_triggered_rule?: string | null;
}

export interface RuleInfo {
  name: string;
  description: string;
  enabled: boolean;
}

export interface WafEvent {
  type: string;
  payload: AuditLogEntry;
}
