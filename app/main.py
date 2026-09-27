"""
Main FastAPI Application for magicpin Vera Bot.
Exposes required endpoints:
- GET  /v1/healthz
- GET  /v1/metadata
- POST /v1/context
- POST /v1/tick
- POST /v1/reply
"""

import os
from datetime import datetime, timezone

# Auto-load .env from project root if present
env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.models import (
    HealthResponse,
    MetadataResponse,
    ContextPushRequest,
    ContextPushResponse,
    TickRequest,
    TickResponse,
    ReplyRequest,
    ReplyResponse,
)
from app.storage import store
from app.decision_engine import decision_engine
from app.reply_engine import reply_engine

app = FastAPI(
    title="Vera — magicpin Merchant AI Assistant",
    description="Intelligent merchant engagement and automated messaging engine for magicpin.",
    version="1.0.0"
)

# Allow CORS for browser tooling or testing dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def root_info():
    """Root info page displaying service status and API documentation."""
    return {
        "service": "Vera — magicpin Merchant AI Assistant",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "health": "/v1/healthz",
            "metadata": "/v1/metadata",
            "context": "/v1/context",
            "tick": "/v1/tick",
            "reply": "/v1/reply"
        },
        "description": "API backend for magicpin merchant automated engagement assistant."
    }


@app.get("/v1/healthz", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Liveness and readiness check."""
    return HealthResponse(
        status="ok",
        service="vera-magicpin",
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@app.get("/v1/metadata", response_model=MetadataResponse, tags=["Metadata"])
def get_metadata():
    """Bot metadata endpoint for judge identification."""
    return MetadataResponse(
        team_name="Vera-Engineers",
        model="vera-deterministic-v1",
        version="1.0.0",
        categories_supported=["dentists", "salons", "restaurants", "gyms", "pharmacies"],
        architecture="Deterministic Rule-Engine + Context-Enriched Neural Formatter"
    )


@app.post("/v1/context", response_model=ContextPushResponse, status_code=status.HTTP_200_OK, tags=["Context"])
def receive_context(request: ContextPushRequest):
    """
    Ingests context from the simulator or production pipelines.
    Scopes: category, merchant, trigger, customer.
    """
    store.set_context(
        scope=request.scope,
        context_id=request.context_id,
        payload=request.payload,
        version=request.version
    )
    return ContextPushResponse(
        accepted=True,
        scope=request.scope,
        context_id=request.context_id,
        message="Context stored successfully"
    )


@app.post("/v1/tick", response_model=TickResponse, status_code=status.HTTP_200_OK, tags=["Tick"])
def handle_tick(request: TickRequest):
    """
    Periodic tick trigger. Evaluates available triggers, selects highest ROI opportunity,
    and returns deterministic composed messages.
    """
    actions = decision_engine.evaluate_triggers(request.available_triggers)
    return TickResponse(actions=actions)


@app.post("/v1/reply", response_model=ReplyResponse, status_code=status.HTTP_200_OK, tags=["Reply"])
def handle_reply(request: ReplyRequest):
    """
    Multi-turn conversation reply endpoint. Handles replies, auto-replies, objections,
    and intent commitment transitions.
    """
    return reply_engine.handle_reply(
        conversation_id=request.conversation_id,
        merchant_id=request.merchant_id,
        message=request.message,
        turn_number=request.turn_number,
        from_role=request.from_role
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
