"""
Comprehensive unit and integration test suite for Vera Bot.
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.storage import store

client = TestClient(app)
DATASET_DIR = Path(__file__).parent.parent / "dataset"


def setup_module():
    """Load categories, merchants, and triggers into test store."""
    store.clear()
    
    # Load categories
    cat_dir = DATASET_DIR / "categories"
    if cat_dir.exists():
        for f in cat_dir.glob("*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            slug = data.get("slug", f.stem)
            client.post("/v1/context", json={
                "scope": "category",
                "context_id": slug,
                "version": 1,
                "payload": data
            })

    # Load merchants
    m_file = DATASET_DIR / "merchants_seed.json"
    if m_file.exists():
        m_data = json.loads(m_file.read_text(encoding="utf-8"))
        for m in m_data.get("merchants", []):
            client.post("/v1/context", json={
                "scope": "merchant",
                "context_id": m["merchant_id"],
                "version": 1,
                "payload": m
            })

    # Load triggers
    t_file = DATASET_DIR / "triggers_seed.json"
    if t_file.exists():
        t_data = json.loads(t_file.read_text(encoding="utf-8"))
        for t in t_data.get("triggers", []):
            client.post("/v1/context", json={
                "scope": "trigger",
                "context_id": t["id"],
                "version": 1,
                "payload": t
            })


def test_healthz():
    resp = client.get("/v1/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_metadata():
    resp = client.get("/v1/metadata")
    assert resp.status_code == 200
    data = resp.json()
    assert "team_name" in data
    assert "model" in data


def test_tick_generation():
    trigger_keys = list(store.triggers.keys())[:3]
    resp = client.post("/v1/tick", json={
        "available_triggers": trigger_keys
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "actions" in data
    assert len(data["actions"]) > 0

    action = data["actions"][0]
    assert "body" in action
    assert "cta" in action
    assert "suppression_key" in action
    assert "rationale" in action
    assert action["send_as"] == "vera"
    
    # Check no taboo words
    taboos = ["blast", "spam", "dump", "leads", "funnel", "algorithm", "conversion hack"]
    for word in taboos:
        assert word not in action["body"].lower()


def test_auto_reply_detection():
    mid = list(store.merchants.keys())[0] if store.merchants else "m_001_drmeera_dentist_delhi"
    resp = client.post("/v1/reply", json={
        "conversation_id": "conv_test_auto_1",
        "merchant_id": mid,
        "message": "Thank you for contacting us! Our team will respond shortly.",
        "turn_number": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "end"


def test_hostile_handling():
    mid = list(store.merchants.keys())[0] if store.merchants else "m_001_drmeera_dentist_delhi"
    resp = client.post("/v1/reply", json={
        "conversation_id": "conv_test_hostile_1",
        "merchant_id": mid,
        "message": "Stop messaging me. This is useless spam.",
        "turn_number": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "end"
    assert "apolog" in data["body"].lower() or "won't" in data["body"].lower() or "sorry" in data["body"].lower()


def test_intent_transition_to_action_mode():
    mid = list(store.merchants.keys())[0] if store.merchants else "m_001_drmeera_dentist_delhi"
    resp = client.post("/v1/reply", json={
        "conversation_id": "conv_test_intent_1",
        "merchant_id": mid,
        "message": "Ok lets do it. Whats next?",
        "turn_number": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "send"
    
    body_lower = data["body"].lower()
    actioning = ["done", "sending", "draft", "here", "confirm", "proceed", "next"]
    qualifying = ["would you", "do you", "can you tell", "what if", "how about"]
    
    assert any(w in body_lower for w in actioning), f"Expected actioning words in: {data['body']}"
    assert not any(w in body_lower for w in qualifying), f"Did not expect qualifying words in: {data['body']}"


def test_cost_inquiry():
    mid = list(store.merchants.keys())[0] if store.merchants else "m_001_drmeera_dentist_delhi"
    resp = client.post("/v1/reply", json={
        "conversation_id": "conv_test_cost_1",
        "merchant_id": mid,
        "message": "How much will this cost?",
        "turn_number": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "send"
    assert "₹" in data["body"] or "price" in data["body"].lower() or "cost" in data["body"].lower()

