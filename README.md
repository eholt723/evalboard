# EvalBoard

LLM evaluation and prompt testing dashboard. Define test cases with inputs, expected outputs, and scoring criteria — then run them against one or more Groq models simultaneously. Results are scored by an LLM-as-judge and stream live to the UI via SSE. Track pass rates and score trends over time.

![CI](https://github.com/eholt723/evalboard/actions/workflows/ci.yml/badge.svg)

## Features

- Define test suites and individual test cases (input, expected output, criteria)
- Run suites against any Groq model — multiple models in parallel for side-by-side comparison
- LLM-as-judge scoring: each result gets a score (1–10), pass/fail, strengths, weaknesses, and reasoning
- Live SSE stream — scores populate in real time as inference completes
- Prompt variant management with auto-versioning
- Dashboard with pass rate and score trend charts

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, FastAPI 0.115, Uvicorn 0.32 |
| Frontend | React 19, Vite 8, Tailwind CSS 4, Recharts 3 |
| LLM Inference | Groq SDK 0.12 (llama-3.1-8b-instant, llama-3.3-70b-versatile) |
| LLM Judge | Groq — llama-3.3-70b-versatile at temperature 0.1 |
| Database | PostgreSQL (Neon serverless), SQLAlchemy 2 async, asyncpg 0.30 |
| Migrations | Alembic 1.14 |
| Real-time | Server-Sent Events via sse-starlette 2.1 |
| Validation | Pydantic 2.10, pydantic-settings 2.6 |
| Routing | React Router 7 |

## Project Structure

```
evalboard/
  backend/
    app/
      main.py             # FastAPI entry point, CORS, router registration
      config.py           # pydantic-settings, reads .env
      db/
        database.py       # async SQLAlchemy engine, session factory, Base
        base.py           # declarative Base (split to avoid alembic/asyncpg conflict)
      models/             # ORM models: TestSuite, TestCase, PromptVariant, Run, RunResult, RunSummary
      schemas/            # Pydantic request/response schemas for all resources
      routers/
        suites.py         # CRUD for test suites and test cases
        prompts.py        # CRUD for prompt variants (auto-versioned by name)
        runs.py           # POST /runs starts background execution; GET /runs/{id}/stream SSE
        dashboard.py      # aggregate queries: pass rates, score trends, model comparison
      engine/
        judge.py          # LLM-as-judge via Groq — returns score, pass, strengths, weaknesses, reasoning
        runner.py         # asyncio parallel execution (semaphore=5), writes RunResult + RunSummary
    migrations/           # Alembic migration scripts
    requirements.txt
  frontend/
    src/
      App.jsx             # route definitions
      components/
        Layout.jsx        # shared nav shell
      pages/
        Dashboard.jsx     # pass rate + trend charts
        Suites.jsx        # list and create test suites
        SuiteDetail.jsx   # test cases within a suite, trigger runs
        RunView.jsx       # live SSE score stream for a run
        Prompts.jsx       # prompt variant CRUD
        About.jsx         # project overview and tech stack
      lib/
        api.js            # fetch wrappers for all backend endpoints
    package.json
    vite.config.js
```

## Architecture

```
Browser
  │
  │  REST (JSON)          SSE stream
  ▼                           │
┌─────────────────────────────┴──────────┐
│              FastAPI (Uvicorn)          │
│                                         │
│  ┌──────────┐  ┌──────────┐            │
│  │  Routers │  │ SSE Fan- │            │
│  │ (CRUD +  │  │  out /   │            │
│  │  /runs)  │  │ broadcaster│          │
│  └────┬─────┘  └──────────┘            │
│       │  background task               │
│  ┌────▼──────────────────┐             │
│  │       Runner          │             │
│  │  asyncio + semaphore  │             │
│  │  (CONCURRENCY = 5)    │             │
│  └──────┬──────────┬─────┘             │
│         │          │                   │
│  ┌──────▼──┐  ┌────▼────┐             │
│  │  Groq   │  │  Judge  │             │
│  │Inference│  │ (Groq)  │             │
│  └──────┬──┘  └────┬────┘             │
│         └────┬──────┘                  │
│         ┌────▼────┐                    │
│         │Postgres │                    │
│         │ (Neon)  │                    │
│         └─────────┘                    │
└────────────────────────────────────────┘
```

| Layer | Responsibility |
|---|---|
| Routers | Validate requests, authorize CRUD, enqueue background runs |
| Runner | Fan out test cases in parallel, enforce concurrency limit, persist results |
| Groq Inference | Execute model completions against the target model under test |
| Judge | Score each response 1–10, emit pass/fail + reasoning via a separate Groq call |
| SSE Broadcaster | Fan out result events to all connected browser clients in real time |
| SQLAlchemy / asyncpg | Async ORM layer over Neon PostgreSQL |
| React Frontend | Render live scores, charts, and suite/prompt management UI |

## Local Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GROQ_API_KEY and DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`, backend at `http://localhost:8000`.

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for inference and judging |
| `DATABASE_URL` | Async PostgreSQL URL (`postgresql+asyncpg://...`) |

## Created by Eric Holt
