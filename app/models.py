"""
Pydantic models for API request and response validation.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field


# --- Context Endpoint Models ---
class ContextPushRequest(BaseModel):
    scope: Literal["category", "merchant", "trigger", "customer"]
    context_id: str
    version: int = 1
    payload: Dict[str, Any]
    delivered_at: Optional[str] = None


class ContextPushResponse(BaseModel):
    accepted: bool
    scope: str
    context_id: str
    message: Optional[str] = "Context stored successfully"


# --- Tick Endpoint Models ---
class TickRequest(BaseModel):
    now: Optional[str] = None
    available_triggers: List[str] = Field(default_factory=list)


class ActionItem(BaseModel):
    trigger_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    body: str
    cta: str
    send_as: str = "vera"
    suppression_key: str
    rationale: str


class TickResponse(BaseModel):
    actions: List[ActionItem] = Field(default_factory=list)


# --- Reply Endpoint Models ---
class ReplyRequest(BaseModel):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    from_role: Literal["merchant", "customer"] = "merchant"
    message: str
    received_at: Optional[str] = None
    turn_number: int = 1


class ReplyResponse(BaseModel):
    action: Literal["send", "wait", "end"]
    body: Optional[str] = ""
    wait_seconds: Optional[int] = 0
    conversation_state: Optional[str] = None


# --- Metadata & Health Models ---
class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "vera-magicpin"
    timestamp: str


class MetadataResponse(BaseModel):
    team_name: str = "Vera-Engineers"
    model: str = "vera-decision-engine-v1"
    version: str = "1.0.0"
    categories_supported: List[str] = ["dentists", "salons", "restaurants", "gyms", "pharmacies"]
    architecture: str = "Deterministic Rule-Engine + Context-Enriched Neural Formatter"
