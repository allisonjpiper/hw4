# Campus Customs — Shop + Chatbot (MGT409 Homework 4)

A Yale-apparel storefront (React + Vite + TypeScript) with a shop chatbot built as a PydanticAI agent behind FastAPI. The agent answers product, price, and stock questions straight from the database, updates the Products page from chat, remembers logged-in customers, and logs every run to `output/audit_trail.json`.

## 1. Add the data pack (local only, not in git)

Place the course data pack inside this folder:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/        # product images referenced by the database
```

## 2. Add your API key

```bash
cp .env.example .env
```

Then edit `.env` and set `PORTKEY_API_KEY`. The agent calls `gpt-5.6-luna` through Portkey.

## 3. Run the backend (FastAPI, port 8000)

From this `hw4/` folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

## 4. Run the frontend (Vite, port 5173)

In a second terminal, from this `hw4/` folder:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The frontend proxies `/api` and `/media` to the backend, so both must be running.

Test account (from the seed database): `test@campuscustoms.yale.edu` / `password`

## Where things are

| Path | What it is |
|---|---|
| `backend/main.py` | FastAPI app: products, auth, chat, and chat-history routes |
| `backend/agent.py` | PydanticAI agent setup, tools, usage limits, audit logging |
| `backend/tools.py` | Database access, tool logic, chat persistence, audit trail |
| `backend/models.py` | Pydantic types for products, chat, context, and audit records |
| `backend/prompts/prompt.md` | System prompt: voice, tool rules, safety rules |
| `output/harness.md` | Full technical write-up: tables, tools, models, safety, limits |
| `output/usability.md`, `output/design.md` | Problem 9 and 10 write-ups |
| `output/app_check.html` | Problem 11 app check, with screenshots in `output/app_check_images/` |
| `output/audit_trail.json` | Append-only log of agent runs |
| `AI_prompts.md` | The prompts used for each problem |
