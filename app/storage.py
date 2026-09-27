"""
In-memory and persistent context storage for Vera.
Handles categories, merchants, triggers, customers, and conversation histories.
"""

from typing import Dict, Any, Optional, List
from threading import Lock
from datetime import datetime, timezone


class ContextStore:
    def __init__(self):
        self._lock = Lock()
        self.categories: Dict[str, Dict[str, Any]] = {}
        self.merchants: Dict[str, Dict[str, Any]] = {}
        self.triggers: Dict[str, Dict[str, Any]] = {}
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.suppressions: Dict[str, datetime] = {}

    def set_context(self, scope: str, context_id: str, payload: Dict[str, Any], version: int = 1):
        with self._lock:
            if scope == "category":
                self.categories[context_id] = payload
            elif scope == "merchant":
                self.merchants[context_id] = payload
            elif scope == "trigger":
                self.triggers[context_id] = payload
            elif scope == "customer":
                self.customers[context_id] = payload

    def get_category(self, slug: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.categories.get(slug)

    def get_merchant(self, merchant_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.merchants.get(merchant_id)

    def get_trigger(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.triggers.get(trigger_id)

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.customers.get(customer_id)

    def record_turn(self, conversation_id: str, role: str, message: str, meta: Optional[Dict[str, Any]] = None):
        with self._lock:
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            self.conversations[conversation_id].append({
                "role": role,
                "message": message,
                "meta": meta or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.conversations.get(conversation_id, []))

    def is_suppressed(self, suppression_key: str) -> bool:
        with self._lock:
            return suppression_key in self.suppressions

    def set_suppression(self, suppression_key: str):
        with self._lock:
            self.suppressions[suppression_key] = datetime.now(timezone.utc)

    def clear(self):
        with self._lock:
            self.categories.clear()
            self.merchants.clear()
            self.triggers.clear()
            self.customers.clear()
            self.conversations.clear()
            self.suppressions.clear()


# Global Singleton Store Instance
store = ContextStore()
