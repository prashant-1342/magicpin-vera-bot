#!/usr/bin/env python3
"""
Interactive CLI to chat with Vera as a merchant in real-time.
"""

import sys
import json
import urllib.request
import urllib.error

# Configure UTF-8 encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Default to your live Render bot or local server
DEFAULT_URL = "https://magicpin-vera-bot-jske.onrender.com"


class VeraChatClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.conv_id = "conv_interactive_demo"
        self.turn = 1
        self.merchant_id = "m_001_drmeera_dentist_delhi"

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.read().decode('utf-8')}"}
        except Exception as e:
            return {"error": str(e)}

    def start(self):
        print("\n" + "=" * 65)
        print("          VERA AI MERCHANT ASSISTANT — INTERACTIVE CHAT")
        print("=" * 65)
        print(f"Connected to: {self.base_url}")
        print("Role: Merchant (Dr. Meera Dental Clinic, Lajpat Nagar)")
        print("-" * 65)
        print("Type your message below and press Enter.")
        print("Commands: 'tick' (to generate initial trigger nudge), 'exit' (to quit)")
        print("=" * 65 + "\n")

        # Start with tick or intro
        print("Vera: Hello Dr. Meera! 190 people in Lajpat Nagar searched for 'Dental Check Up' in the past 48 hours. Want me to send them your ₹299 Dental Cleaning offer?\n")

        while True:
            try:
                user_msg = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting chat. Bye!")
                break

            if not user_msg:
                continue

            if user_msg.lower() in ("exit", "quit", "q"):
                print("\nExiting chat. Bye!")
                break

            if user_msg.lower() == "tick":
                res = self._post("/v1/tick", {"available_triggers": ["trg_001_research_digest_dentists"]})
                actions = res.get("actions", [])
                if actions:
                    print(f"\nVera: {actions[0].get('body')}\n")
                else:
                    print("\nVera: No pending triggers at this moment.\n")
                continue

            # Send merchant reply
            self.turn += 1
            payload = {
                "conversation_id": self.conv_id,
                "merchant_id": self.merchant_id,
                "customer_id": None,
                "from_role": "merchant",
                "message": user_msg,
                "turn_number": self.turn
            }

            resp = self._post("/v1/reply", payload)
            if "error" in resp:
                print(f"\n[Connection Error: {resp['error']}]\n")
                continue

            action = resp.get("action", "send")
            body = resp.get("body", "")

            print(f"\nVera [{action.upper()}]: {body}\n")

            if action == "end":
                print("[Conversation marked as ENDED by Vera]\n")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    client = VeraChatClient(url)
    client.start()
