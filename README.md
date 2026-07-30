# Agent WAF — Web Application Firewall for AI Agents

An enterprise-grade, policy-enforcing security proxy layer that sits between AI Agents and their toolkits. It intercepts, evaluates, filters, logs, and audits every tool call invocation in real time before execution.

---

## 🏛️ System Architecture Diagram

```mermaid
graph TD
    User([User / Client]) -->|POST /agent/chat| ChatPage[Sample AI Agent React UI]
    ChatPage --> Orchestrator[Agent Orchestrator]
    Orchestrator --> Planner[Agent Planner]
    Planner -->|ToolInvocation| Proxy[Agent WAF Proxy Interceptor]
    
    subgraph Security Layer - Policy Engine
        Proxy --> Engine[Policy Engine]
        Engine --> R1[RateLimitRule]
        Engine --> R2[ParameterValidationRule]
        Engine --> R3[DataScopeRule]
        Engine --> R4[SequenceRule]
    end

    Engine -->|Allowed| Executor[Tool Executor]
    Engine -->|Blocked| BlockResponse[WAF Security Block Response]
    
    Executor --> Registry[Tool Registry]
    Registry --> Tool[Target Tool: Calculator / Search / File]

    Proxy --> DB[(SQLite Audit Log DB)]
    Proxy --> Metrics[Metrics Collector]
    Metrics --> WS[WebSocket Event Publisher]
    WS -->|Live Stream| Dashboard[React WAF Dashboard /dashboard]
```

---

## 🚀 Key Features & Security Rules

1. **Rate Limit Rule (`RateLimitRule`)**:
   - Limits per Agent + Tool execution velocity over a rolling sliding window (e.g. 5 calls/min).
2. **Parameter Validation Rule (`ParameterValidationRule`)**:
   - Recursively inspects payload fields to detect SQL Injection (`DROP TABLE`, `UNION SELECT`), Prompt Injection (`Ignore previous instructions`), Path Traversal (`../../../etc/passwd`), and oversized payloads.
3. **Data Scope Rule (`DataScopeRule`)**:
   - Conﬁnes resource access parameters (`filename`, `path`, `filepath`, `resource`) strictly within declared allowed scopes (e.g., `sample_data/`).
4. **Sequence Rule (`SequenceRule`)**:
   - Enforces session-based execution dependencies (e.g. `file_reader` must be preceded by a `search` in the same session).
5. **Real-time Monitoring Dashboard**:
   - Interactive React + Vite interface with live KPI cards, Recharts visualizations, live pipeline request flows, tool traffic counts, rule hit breakdown, and instant WebSockets streaming.
6. **Shadow Mode**:
   - Configurable `SHADOW_MODE=true` mode that logs violations as `would_block=true` without blocking actual execution.

---

## 🛠️ Quickstart & Local Setup

### Backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```
* API Server: `http://localhost:8000`
* Swagger OpenAPI Docs: `http://localhost:8000/docs`

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
* Web Dashboard: `http://localhost:5173/dashboard`
* Sample AI Agent Chat: `http://localhost:5173/chat`

---

## 🧪 Running Automated Test Suite
```bash
python -m pytest backend/tests
```

---

## 🐳 Docker Deployment
```bash
docker-compose up --build
```

---

## 📡 REST API Endpoint Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness health check |
| `GET` | `/ready` | Readiness check |
| `POST` | `/agent/chat` | Main Agent interaction endpoint |
| `GET` | `/metrics` | Returns in-memory WAF metrics & counters |
| `GET` | `/audit` | Retrieves historical audit logs from SQLite |
| `GET` | `/rules` | Lists registered security rules & config |
| `POST` | `/rules/reload` | Reloads rules configuration |
| `WS` | `/dashboard/ws` | Live WebSocket event stream |

---

## 🛡️ Enterprise Confidentiality
* Developed for **Aivar Innovations**.