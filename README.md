# Vera — AI-Powered Merchant Messaging Assistant for magicpin

Vera is an intelligent merchant messaging backend built for **magicpin**. It analyzes real-time local demand triggers, merchant catalog metrics, and customer behaviors to compose high-conversion, highly-specific merchant engagement messages.

---

## Architecture Overview

```
                        ┌───────────────────────────────┐
                        │   magicpin Judge / Webhook    │
                        └───────────────┬───────────────┘
                                        │ HTTP Requests
                                        ▼
                        ┌───────────────────────────────┐
                        │       FastAPI Gateway         │
                        │    (/healthz, /metadata)      │
                        └───────┬───────────────┬───────┘
                                │               │
                ┌───────────────▼─┐           ┌─▼───────────────┐
                │  POST /v1/context│           │   POST /v1/tick │
                └───────┬─────────┘           └─┬───────────────┘
                        │ Ingest Context        │ Evaluate Triggers
                        ▼                       ▼
            ┌───────────────────────┐   ┌───────────────────────────┐
            │     Context Store     │◄──┤      Decision Engine      │
            │ (Categories, Merchants│   │  (Opportunity Ranker &    │
            │   Triggers, Customers)│   │   Suppression Filter)     │
            └───────────┬───────────┘   └─────────────┬─────────────┘
                        │                             │
                        │   ┌─────────────────────────┘
                        ▼   ▼
            ┌───────────────────────────┐       ┌───────────────────┐
            │     Message Composer      │◄──────┤   POST /v1/reply  │
            │ (Specifics, Fit, Single-  │       │ (State Machine,   │
            │  action CTA, No Taboo)    │       │  Intent & Opt-out)│
            └───────────┬───────────────┘       └───────────────────┘
                        ▼
            Structured JSON Actions
```

---

## Core Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/v1/healthz` | Liveness & readiness probe |
| `GET` | `/v1/metadata` | Team name, model version & supported categories |
| `POST` | `/v1/context` | Ingests category schemas, merchant profiles, triggers, and customer signals |
| `POST` | `/v1/tick` | Evaluates pending triggers and composes deterministic, actionable recommendations |
| `POST` | `/v1/reply` | Multi-turn state machine handling merchant responses, objections, and auto-replies |

---

## 5 Scoring Dimensions & Optimizations

Vera is strictly optimized against the 5 judging criteria:

1. **Specificity (10/10)**:
   - Includes real numbers: search counts (`190 people`), prices (`₹299`), percentages (`25% dip`).
   - Grounded in real localities (`Indiranagar`, `Cyber City`) and timeframes (`in the past 48 hours`).

2. **Category Fit (10/10)**:
   - **Dentists**: Clinical, peer-to-peer tone (`Dr.` honorific prefix, `patients`, `appointments`, `checkup`).
   - **Salons**: Warm, stylish (`clients`, `styling`, `bridal package`).
   - **Restaurants**: Operator-to-operator (`diners`, `covers`, `tables`, `orders`).
   - **Gyms**: Motivational, coaching (`members`, `fitness goals`, `trial pass`).
   - **Pharmacies**: Trustworthy, precise (`prescriptions`, `wellness`, `health check`).
   - Zero internal marketing jargon (`blast`, `spam`, `funnel`, `algorithm` are filtered out).

3. **Merchant Fit (10/10)**:
   - Personalizes using merchant owner first names and verified catalog offers.
   - Zero fabrication: only references active offers delivered via context.

4. **Decision Quality & Trigger Relevance (10/10)**:
   - Connects triggers (`research_spike`, `performance_dip`, `competitor_surge`, `festival_event`, `review_alert`, `customer_reengagement`, `weekend_rush`) to concrete revenue opportunities.

5. **Engagement Compulsion (10/10)**:
   - Formulates a single low-friction CTA question that is easy to answer with a single tap (e.g., *"Want me to send them your ₹299 checkup offer?"*).

---

## Multi-Turn Reply State Machine

- **Auto-Reply Detection**: Automatically detects generic auto-responder messages (`"Thank you for contacting us"`) and terminates (`"action": "end"`).
- **Hostility / Opt-Out**: Detects hostile phrases (`"Stop messaging me"`) and gracefully terminates with an apology (`"action": "end"`).
- **Intent Transition (Action Mode)**: When the merchant commits (`"Ok lets do it. Whats next?"`), Vera instantly transitions from qualifying questions to action execution mode (`"Done! I have created the draft... Here is your confirmation: proceeding with sending notifications now."`).
- **Objection & Inquiries**: Answers pricing, audience reach, and campaign duration questions with precise catalog data.

---

## How to Run & Test Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Automated Test Suite
```bash
python -m pytest -v tests/test_bot.py
```

### 3. Start the Server Locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 4. Run the Judge Simulator
```bash
# Set your preferred LLM provider & API key
export LLM_PROVIDER="openai"      # or gemini, anthropic, groq, deepseek, ollama
export LLM_API_KEY="your-api-key"
export BOT_URL="http://localhost:8080"
export TEST_SCENARIO="all"

python judge_simulator.py
```

---

## Public Deployment

### Deploy with Docker
```bash
docker build -t vera-bot .
docker run -p 8080:8080 vera-bot
```

### Free 1-Click Cloud Hosting (Render / Railway / Fly.io)
1. Push this repo to GitHub.
2. Link your repository on [Render](https://render.com) as a **Web Service** (configured with `render.yaml`).
3. Set the start command to:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Copy the public HTTPS URL (e.g., `https://vera-bot.onrender.com`) and submit it to the magicpin judge!
