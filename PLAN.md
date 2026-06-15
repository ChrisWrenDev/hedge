# Hedge — Implementation Plan

Options convexity ranking and hedging system built as a modular monolith.

## Architecture Overview

```
Market Data Sources (IBKR, Polygon, CBOE, Yahoo)
        ↓
Data Ingestion Layer (APScheduler, 5-15 min intervals)
        ↓
Options Data Store (PostgreSQL / TimescaleDB)
        ↓
Pricing / Greeks Engine (vollib — Black-Scholes, Greeks, IV)
        ↓
Scenario Engine (stress tests, what-if, Monte Carlo)
        ↓
Convexity Ranking Engine (score options by convexity profile)
        ↓
Portfolio / Budget Engine (position sizing, Greeks aggregation)
        ↓
Decision Rules Engine (code-based rules + YAML config + DB audit)
        ↓
Dashboard + Alerts (Next.js frontend + email/webhook)
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Recharts |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 / TimescaleDB |
| Migrations | Alembic |
| Scheduler | APScheduler (in-process) |
| Options Pricing | vollib (Black-Scholes, Greeks, IV) |
| Data Sources | ib_async (IBKR), polygon-api-client, yfinance, requests |
| Alerts | aiosmtplib (email), httpx (webhooks) |
| Config | Pydantic Settings, YAML (strategies) |

## Project Structure

```
hedge/
├── docker-compose.yml
├── .env.example
├── PLAN.md
├── docs/
│   ├── architecture.md
│   ├── database-schema.md
│   ├── rules-engine.md
│   ├── pipeline.md
│   ├── modules.md
│   ├── dashboard.md
│   └── dependencies.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   ├── strategies/              # YAML strategy configs
│   └── app/
│       ├── main.py              # FastAPI + APScheduler lifespan
│       ├── config.py
│       ├── database.py
│       ├── pipeline.py          # Orchestrator
│       └── modules/
│           ├── data_sources/    # IBKR, Polygon, CBOE, Yahoo adapters
│           ├── ingestion/       # Fetch + normalize + store
│           ├── options_data/    # Core data models + queries
│           ├── pricing/         # Greeks + IV + theoretical pricing
│           ├── scenarios/       # Stress tests + what-if
│           ├── convexity/       # Convexity scoring + ranking
│           ├── portfolio/       # Positions + risk budgets
│           ├── rules/           # Decision rules engine
│           ├── alerts/          # Email + webhook notifications
│           └── dashboard/       # Aggregated API for frontend
└── frontend/
    └── src/
        ├── app/                 # App Router pages
        ├── components/          # Recharts + React components
        └── lib/                 # API client + types
```

## Implementation Phases

| Phase | Modules | Description |
|---|---|---|
| **1** | data_sources, ingestion, options_data | Data pipeline foundation |
| **2** | pricing, convexity | Core analytics engine |
| **3** | portfolio, rules | Portfolio tracking + decision engine |
| **4** | scenarios, alerts | Stress testing + notifications |
| **5** | dashboard (frontend) | Full dashboard UI |
| **6** | dashboard (backend API), integration | API layer + end-to-end testing |

Each phase is independently functional.

## Getting Started

```bash
cp .env.example .env
docker compose up
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Detailed Docs

- [Architecture](docs/architecture.md)
- [Database Schema](docs/database-schema.md)
- [Module Breakdown](docs/modules.md)
- [Pipeline Orchestration](docs/pipeline.md)
- [Rules Engine](docs/rules-engine.md)
- [Dashboard Pages](docs/dashboard.md)
- [Dependencies](docs/dependencies.md)
