from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.api.endpoints import router as agent_router

app = FastAPI(
    title="Agent WAF API",
    description="Production-ready Agent WAF Backend",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the agent chat router
app.include_router(agent_router)


@app.get("/")
async def root():
    return {
        "message": "Agent WAF API is running",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "agent-waf",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready")
async def readiness():
    return {
        "status": "ready"
    }