import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from app.core.config import settings
from app.api.endpoints import router as agent_router

# Configure application logger
logger = logging.getLogger("agent_waf")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

app = FastAPI(
    title="Agent WAF API",
    description="Production-ready Agent WAF Backend",
    version="1.0.0"
)

# CORS Configuration
# Ensure wildcard '*' is removed when allow_credentials=True is active
origins = [o for o in settings.ALLOWED_ORIGINS if o != "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred."}
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