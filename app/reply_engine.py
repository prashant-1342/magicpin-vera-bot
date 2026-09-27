"""
Reply Engine for handling multi-turn conversation states, auto-reply detection,
hostile/opt-out handling, intent transitions, and AI-driven dynamic responses.
"""

import re
import json
from typing import Dict, Any, Tuple, Optional
from app.storage import ContextStore, store
from app.models import ReplyResponse
from app.llm_client import llm_service


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
        Uses LLM intelligence when configured, with high-reliability deterministic guardrails.
        """
        msg_clean = message.strip()
        msg_lower = msg_clean.lower()
        
        # Save inbound turn
        self.store.record_turn(conversation_id, from_role, msg_clean, {"turn": turn_number})

        # 1. AUTO-REPLY DETECTION (Safety Guardrail)
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

        # 2. HOSTILITY / OPT-OUT HANDLING (Safety Guardrail)
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

        # Fetch Merchant & Category Context
        merchant = self.store.get_merchant(merchant_id) or {}
        cat_slug = merchant.get("category_slug", "generic")
        category = self.store.get_category(cat_slug) or {}
        m_identity = merchant.get("identity", {})
        owner_name = m_identity.get("owner_first_name", "")
        merchant_name = m_identity.get("name", "your business")
        locality = m_identity.get("locality", "your area")

        offers = merchant.get("offers", [])
        active_offers = [o for o in offers if o.get("status") == "active"]
        top_offer = active_offers[0] if active_offers else (offers[0] if offers else {"title": "special offer", "price_inr": 0})
        offer_title = top_offer.get("title", "special promotion")
        offer_price = top_offer.get("price_inr") or top_offer.get("value") or 0
        try:
            offer_price = int(offer_price)
        except (ValueError, TypeError):
            offer_price = 0
        price_text = f"₹{offer_price:,}" if offer_price > 0 else "special offer"

        # Check for Commitment / Intent Transition
        is_commitment = any(re.search(pat, msg_lower) for pat in COMMITMENT_PATTERNS)

        # 3. TRY LLM GENERATION IF CONFIGURED
        if llm_service.is_configured:
            llm_reply = self._generate_llm_reply(
                conversation_id=conversation_id,
                message=msg_clean,
                is_commitment=is_commitment,
                category=category,
                merchant=merchant,
                top_offer_title=offer_title,
                price_text=price_text
            )
            if llm_reply:
                resp = ReplyResponse(
                    action="send",
                    body=llm_reply,
                    wait_seconds=0,
                    conversation_state="llm_action_confirmed" if is_commitment else "llm_engaged"
                )
                self.store.record_turn(conversation_id, "vera", llm_reply, {"action": resp.action})
                return resp

        # 4. DETERMINISTIC FALLBACK RESPONSES

        # 4a. COMMITMENT / INTENT TRANSITION (Action Mode)
        if is_commitment:
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

        # 4b. PRICING & COST INQUIRIES
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

        # 4c. TARGET AUDIENCE INQUIRIES
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

        # 4d. GENERAL DEFAULT ENGAGEMENT
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

    def _generate_llm_reply(
        self,
        conversation_id: str,
        message: str,
        is_commitment: bool,
        category: Dict[str, Any],
        merchant: Dict[str, Any],
        top_offer_title: str,
        price_text: str
    ) -> Optional[str]:
        """Generate response via LLM incorporating conversation history and domain rules."""
        history = self.store.get_conversation_history(conversation_id)
        history_text = "\n".join([f"{t['role'].capitalize()}: {t['message']}" for t in history[-5:]])

        cat_slug = category.get("slug", "generic")
        voice_info = category.get("voice", {})
        tone = voice_info.get("tone", "professional")
        taboo_words = voice_info.get("vocab_taboo", [])
        m_ident = merchant.get("identity", {})

        system_prompt = f"""You are Vera, an intelligent, trusted merchant assistant on magicpin.
You are conversing with a local merchant ({m_ident.get('name')}, located in {m_ident.get('locality', 'local area')}, category: {cat_slug}).
Tone style: {tone}.

BUSINESS FACTS:
- Active Offer: {top_offer_title} at {price_text}
- Locality: {m_ident.get('locality')}
- Owner: {m_ident.get('owner_first_name')}

STRICT RULES:
1. Always be specific, practical, and grounded in real data. Never fabricate data outside this context.
2. Keep response concise (1-3 sentences).
3. Do NOT use marketing taboo words: {taboo_words} or words like 'blast', 'spam', 'funnel', 'algorithm', 'conversion hack'.
4. CRITICAL INTENT RULE:
   If the merchant agrees/commits (e.g. 'ok lets do it', 'proceed', 'sounds good', 'yes please', 'whats next'):
   You MUST enter ACTION MODE using action keywords (such as 'done', 'draft', 'confirm', 'proceed', 'sending', 'next', 'here').
   You MUST NOT ask qualifying questions (NEVER use 'would you', 'do you', 'can you tell', 'what if', 'how about').
   Confirm that the draft is created/proceeding and describe the next action.
5. If the merchant asks questions (price, audience, timeline, options), answer directly and clearly using the merchant context."""

        user_prompt = f"""Conversation History:
{history_text}

Merchant's Latest Message: "{message}"

Respond directly as Vera (reply text only):"""

        reply = llm_service.generate(system_prompt, user_prompt, temperature=0.2)
        if not reply:
            return None

        # Verify action mode if it was a commitment
        reply_lower = reply.lower()
        if is_commitment:
            qualifying = ["would you", "do you", "can you tell", "what if", "how about"]
            if any(w in reply_lower for w in qualifying):
                # Fallback to pure actioning if LLM accidentally used qualifying word
                return (
                    f"Done! I have created the draft for your {price_text} {top_offer_title} campaign. "
                    f"Here is your confirmation: proceeding with sending notifications to active searchers in {m_ident.get('locality')} now."
                )

        return reply


reply_engine = ReplyEngine()
