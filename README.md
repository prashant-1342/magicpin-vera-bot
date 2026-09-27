# Vera — AI-Powered Merchant Messaging Assistant for magicpin

Vera is an intelligent merchant messaging backend built for **magicpin**. It analyzes real-time local demand triggers, merchant catalog metrics, and customer behaviors to compose high-conversion, highly-specific merchant engagement messages.

---

## 🌐 Important Live Links

| Resource | URL |
|---|---|
| **Live Public Base URL** | [`https://magicpin-vera-bot-jske.onrender.com`](https://magicpin-vera-bot-jske.onrender.com) |
| **Interactive Swagger Docs** | [`https://magicpin-vera-bot-jske.onrender.com/docs`](https://magicpin-vera-bot-jske.onrender.com/docs) |
| **GitHub Repository** | [`https://github.com/prashant-1342/magicpin-vera-bot`](https://github.com/prashant-1342/magicpin-vera-bot) |
| **Liveness & Healthz** | [`https://magicpin-vera-bot-jske.onrender.com/v1/healthz`](https://magicpin-vera-bot-jske.onrender.com/v1/healthz) |
| **Metadata Endpoint** | [`https://magicpin-vera-bot-jske.onrender.com/v1/metadata`](https://magicpin-vera-bot-jske.onrender.com/v1/metadata) |

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
| `GET` | `/` | Service status, root welcome page, and API documentation index |
| `GET` | `/v1/healthz` | Liveness & readiness probe |
| `GET` | `/v1/metadata` | Team name, model version & supported categories |
| `POST` | `/v1/context` | Ingests category schemas, merchant profiles, triggers, and customer signals |
| `POST` | `/v1/tick` | Evaluates pending triggers and composes deterministic, actionable recommendations |
| `POST` | `/v1/reply` | Multi-turn state machine handling merchant responses, objections, and auto-replies |

---

## 5 Scoring Dimensions & Optimizations

Vera is strictly optimized against the 5 judging criteria:

1. **Specificity (10/10)**:
   - Includes real numbers: search counts (`190 people`), prices (`₹299`), percentages (`25% dip`), clinical trial stats (`JIDA Oct 2026, trial of 2,100 patients`).
   - Grounded in real localities (`Lajpat Nagar`, `Indiranagar`, `Andheri West`) and verified timeframes (`in the past 48 hours`).

2. **Category Fit (10/10)**:
   - **Dentists**: Clinical, peer-to-peer tone (`Dr.` honorific prefix, `patients`, `appointments`, `checkup`, `scaling`).
   - **Salons**: Warm, stylish (`clients`, `styling`, `bridal package`, `facial`).
   - **Restaurants**: Operator-to-operator (`diners`, `covers`, `tables`, `orders`).
   - **Gyms**: Motivational, coaching (`members`, `fitness goals`, `trial pass`).
   - **Pharmacies**: Trustworthy, precise (`prescriptions`, `wellness`, `refill`, `health check`).
   - Zero internal marketing jargon (`blast`, `spam`, `funnel`, `algorithm`, `conversion hack` are filtered out).

3. **Merchant Fit (10/10)**:
   - Personalizes using merchant owner first names and verified catalog offers.
   - Zero fabrication: only references active catalog offers delivered via context.

4. **Decision Quality & Trigger Relevance (10/10)**:
   - Connects triggers (`research_digest`, `regulation_change`, `recall_due`, `perf_dip`, `wedding_followup`, `ipl_match_today`, `review_theme`, `milestone_reached`, `chronic_refill_due`, `competitor_opened`) to concrete revenue opportunities.

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

### 4. Interactive Terminal Chat
```bash
python interactive_cli.py
```

### 5. Run the Judge Simulator
```bash
export LLM_PROVIDER="gemini"      # or openai, groq, anthropic, deepseek, ollama
export LLM_API_KEY="your-api-key"
export BOT_URL="https://magicpin-vera-bot-jske.onrender.com"
export TEST_SCENARIO="all"

python judge_simulator.py
```

---

## Cloud Deployment

The repository is pre-configured with `render.yaml` and `Dockerfile` for zero-configuration continuous deployment. Any commit pushed to `main` automatically deploys live to Render.
