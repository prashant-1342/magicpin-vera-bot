"""
Decision engine for prioritizing signals and triggers deterministically.
"""

from typing import List, Dict, Any, Optional
from app.storage import ContextStore, store
from app.composer import compose_message
from app.models import ActionItem


class DecisionEngine:
    def __init__(self, context_store: ContextStore = store):
        self.store = context_store

    def evaluate_triggers(self, trigger_ids: List[str]) -> List[ActionItem]:
        """
        Evaluate a list of trigger IDs and return actionable messages.
        Filters out duplicates, suppressed keys, or incomplete merchant profiles.
        Prioritizes high-urgency and immediate timing over distant triggers.
        """
        actions: List[ActionItem] = []
        seen_merchants = set()

        # Retrieve and rank valid triggers by urgency
        valid_triggers = []
        for tid in trigger_ids:
            trigger = self.store.get_trigger(tid)
            if not trigger:
                continue
            merchant_id = trigger.get("merchant_id")
            if not merchant_id:
                continue
            merchant = self.store.get_merchant(merchant_id)
            if not merchant:
                continue
            
            # Rank score: integer urgency 1-5, or string 'immediate'/'high'/'medium'/'low'
            urgency = trigger.get("urgency", 2)
            if isinstance(urgency, int):
                urgency_score = urgency
            elif isinstance(urgency, str):
                u_lower = urgency.lower()
                urgency_score = 4 if u_lower == "immediate" else (3 if u_lower == "high" else (1 if u_lower == "low" else 2))
            else:
                urgency_score = 2
            valid_triggers.append((urgency_score, tid, trigger, merchant))

        # Sort descending by urgency score
        valid_triggers.sort(key=lambda x: x[0], reverse=True)

        for _, tid, trigger, merchant in valid_triggers:
            merchant_id = merchant.get("merchant_id")
            if merchant_id in seen_merchants:
                continue

            cat_slug = merchant.get("category_slug", "")
            category = self.store.get_category(cat_slug) or {"slug": cat_slug}

            customer_id = trigger.get("customer_id")
            customer = self.store.get_customer(customer_id) if customer_id else None

            # Compose message and metadata
            body, cta, suppression_key, rationale = compose_message(category, merchant, trigger, customer)

            # Check suppression key
            if self.store.is_suppressed(suppression_key):
                continue

            # Record suppression
            self.store.set_suppression(suppression_key)
            seen_merchants.add(merchant_id)

            actions.append(ActionItem(
                trigger_id=tid,
                merchant_id=merchant_id,
                customer_id=customer_id,
                body=body,
                cta=cta,
                send_as="vera",
                suppression_key=suppression_key,
                rationale=rationale
            ))

        return actions


decision_engine = DecisionEngine()
