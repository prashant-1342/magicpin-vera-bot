"""
Reply Engine for handling multi-turn conversation states, auto-reply detection,
hostile/opt-out handling, intent transitions, and merchant inquiries.
"""

import re
from typing import Dict, Any, Tuple
from app.storage import ContextStore, store
from app.models import ReplyResponse


AUTO_REPLY_PATTERNS = [
    r"thank you for contacting",
    r"our team will respond",
    r"we will get back to you",
    r"auto[- ]?generated",
    r"automated message",
    r"out of office",
    r"away from my desk",
    r"currently unavailable",
    r"thank you for reaching out",
    r"do not reply to this email",
    r"this is an automated"
]

HOSTILE_PATTERNS = [
    r"stop messaging",
    r"useless spam",
    r"stop spamming",
    r"don'?t message",
    r"do not contact",
    r"unsubscribe",
    r"leave me alone",
    r"remove my number",
    r"harassment",
    r"report spam"
]

COMMITMENT_PATTERNS = [
    r"let'?s do it",
    r"what'?s next",
    r"go ahead",
    r"proceed",
    r"sounds good",
    r"yes please",
    r"yes let'?s start",
    r"start it",
    r"start campaign",
    r"make it live",
    r"confirm",
    r"okay do it",
    r"ok lets do"
]

COST_PATTERNS = [
    r"how much",
    r"cost",
    r"price",
    r"pricing",
    r"charges",
    r"fee",
    r"budget"
]

AUDIENCE_PATTERNS = [
    r"who will see",
    r"target audience",
    r"reach",
    r"how many people",
    r"who receives"
]


class ReplyEngine:
    def __init__(self, context_store: ContextStore = store):
        self.store = context_store

    def handle_reply(
        self,
        conversation_id: str,
        merchant_id: str,
        message: str,
        turn_number: int = 1,
        from_role: str = "merchant"
    ) -> ReplyResponse:
        """
        Processes an incoming reply and returns an appropriate response action and message body.
        """
        msg_clean = message.strip()
        msg_lower = msg_clean.lower()
        
        # Save inbound turn
        self.store.record_turn(conversation_id, from_role, msg_clean, {"turn": turn_number})

        # 1. AUTO-REPLY DETECTION
        for pattern in AUTO_REPLY_PATTERNS:
            if re.search(pattern, msg_lower):
                resp = ReplyResponse(
                    action="end",
                    body="Auto-reply detected. Ending conversation.",
                    wait_seconds=0,
                    conversation_state="ended_auto_reply"
                )
                self.store.record_turn(conversation_id, "vera", resp.body or "", {"action": resp.action})
                return resp

        # 2. HOSTILITY / OPT-OUT HANDLING
        for pattern in HOSTILE_PATTERNS:
            if re.search(pattern, msg_lower):
                resp = ReplyResponse(
                    action="end",
                    body="Understood. I apologize for reaching out. I won't send further messages to your account.",
                    wait_seconds=0,
                    conversation_state="ended_opt_out"
                )
                self.store.record_turn(conversation_id, "vera", resp.body or "", {"action": resp.action})
                return resp

        # Fetch Merchant Context for personalization
        merchant = self.store.get_merchant(merchant_id) or {}
        offers = merchant.get("offers", [])
        active_offers = [o for o in offers if o.get("status") == "active"]
        top_offer = active_offers[0] if active_offers else (offers[0] if offers else {"title": "special offer", "price_inr": 0})
        offer_title = top_offer.get("title", "special promotion")
        offer_price = top_offer.get("price_inr", 0)
        price_text = f"₹{offer_price:,}" if offer_price > 0 else "standard promotion"
        locality = merchant.get("identity", {}).get("locality", "your area")

        # 3. COMMITMENT / INTENT TRANSITION (Action Mode)
        # Note: Must NOT use qualifying terms like ["would you", "do you", "can you tell", "what if", "how about"]
        # Must USE actioning terms like ["done", "sending", "draft", "here", "confirm", "proceed", "next"]
        for pattern in COMMITMENT_PATTERNS:
            if re.search(pattern, msg_lower):
                body = (
                    f"Done! I have created the draft for your {price_text} {offer_title} campaign. "
                    f"Here is your confirmation: proceeding with sending notifications to active searchers in {locality} now. "
                    f"Next update will arrive once responses start coming in."
                )
                resp = ReplyResponse(
                    action="send",
                    body=body,
                    wait_seconds=0,
                    conversation_state="action_confirmed"
                )
                self.store.record_turn(conversation_id, "vera", body, {"action": resp.action})
                return resp

        # 4. PRICING & COST INQUIRIES
        for pattern in COST_PATTERNS:
            if re.search(pattern, msg_lower):
                if offer_price > 0:
                    body = (
                        f"Your customer offer price is {price_text} for '{offer_title}'. "
                        f"There are no setup fees for this campaign. Ready for me to activate the draft?"
                    )
                else:
                    body = (
                        f"Your {offer_title} campaign has no upfront listing cost. "
                        f"Ready for me to activate the draft?"
                    )
                resp = ReplyResponse(
                    action="send",
                    body=body,
                    wait_seconds=0,
                    conversation_state="inquiry_answered"
                )
                self.store.record_turn(conversation_id, "vera", body, {"action": resp.action})
                return resp

        # 5. TARGET AUDIENCE INQUIRIES
        for pattern in AUDIENCE_PATTERNS:
            if re.search(pattern, msg_lower):
                body = (
                    f"This campaign targets verified nearby users in {locality} who searched for your services in the past 48 hours. "
                    f"Ready for me to activate the draft?"
                )
                resp = ReplyResponse(
                    action="send",
                    body=body,
                    wait_seconds=0,
                    conversation_state="audience_explained"
                )
                self.store.record_turn(conversation_id, "vera", body, {"action": resp.action})
                return resp

        # 6. GENERAL DEFAULT ENGAGEMENT
        body = (
            f"Here is the draft for '{offer_title}' at {price_text} for searchers in {locality}. "
            f"Say 'proceed' whenever you are ready to launch."
        )
        resp = ReplyResponse(
            action="send",
            body=body,
            wait_seconds=0,
            conversation_state="engaged"
        )
        self.store.record_turn(conversation_id, "vera", body, {"action": resp.action})
        return resp


reply_engine = ReplyEngine()
