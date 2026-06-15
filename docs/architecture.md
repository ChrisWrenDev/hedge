# Architecture

## System Overview

Hedge is a modular monolith that ingests options market data, calculates pricing metrics, ranks options by convexity, and generates trade recommendations through a configurable rules engine.

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                               │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│     │   IBKR   │  │ Polygon  │  │   CBOE   │  │  Yahoo   │      │
│     └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│          └─────────────┴─────────────┴─────────────┘            │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                             │
│      Normalize → Deduplicate → Upsert → Track freshness         │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   OPTIONS DATA STORE                            │
│  tickers │ contracts │ bars │ snapshots │ vol_surface │ hv      │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PRICING / GREEKS ENGINE                         │
│  Black-Scholes Greeks │ IV Surface │ Theoretical Pricing        │
└──────────┬──────────────────────────────────────┬───────────────┘
           ▼                                      ▼
┌──────────────────┐                           ┌──────────────────┐
│ SCENARIO ENGINE  │                           │ CONVEXITY ENGINE │
│ Stress tests     │                           │ Score + Rank     │
│ What-if          │                           │ by convexity     │
│ Monte Carlo      │                           │ profile          │
└────────┬─────────┘                           └────────┬─────────┘
         │                                              │
         └────────────────────┬─────────────────────────┘
                              ▼
         ┌──────────────────────────┐
         │   PORTFOLIO / BUDGET     │
         │ Aggregate Greeks         │
         │ Position sizing          │
         │ Risk limits              │
         └────────────┬─────────────┘
                      ▼
         ┌──────────────────────────┐
         │   DECISION RULES ENGINE  │
         │ Code rules + YAML params │
         │ + DB audit trail         │
         └──────┬──────────┬────────┘
                │          │
                ▼          ▼
    ┌───────────┐  ┌──────────────┐
    │  ALERTS   │  │  DASHBOARD   │
    │ Email     │  │  Next.js     │
    │ Webhook   │  │  Recharts    │
    └───────────┘  └──────────────┘
```

## Module Communication

Modules communicate via **direct function calls** (synchronous, in-process). Each module exposes a public `service.py` and `router.py`; other modules import service functions directly.

```
data_sources.service.fetch_polygon()  ← called by ingestion.service
pricing.engine.calculate_greeks()     ← called by pipeline
convexity.engine.score_options()      ← called by pipeline
rules.engine.evaluate_all()           ← called by pipeline
alerts.service.dispatch()             ← called by rules.engine
```

No message broker or event bus — simplicity of the monolith pattern. Can add async events later if modules need further decoupling.

## API Route Structure

All routes are prefixed with `/api`:

```
/api/health                          # Health check
/api/data-sources/                   # Source status, manual triggers
/api/ingestion/                      # Ingestion job status
/api/options/                        # Options chains, snapshots
/api/pricing/                        # Greeks, IV surface
/api/scenarios/                      # Scenario CRUD + run
/api/convexity/                      # Convexity rankings
/api/portfolio/                      # Portfolios, positions
/api/rules/                          # Rules CRUD + trigger history
/api/alerts/                         # Channels, subscriptions, history
/api/dashboard/                      # Aggregated overview data
```

## Scheduler Architecture

APScheduler runs inside the FastAPI process lifespan:

```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(pipeline.run, 'interval', minutes=5,
                      trigger=DateTrigger(start_date=market_open,
                                          end_date=market_close))
    scheduler.start()
    yield
    scheduler.shutdown()
```

Jobs run sequentially within the pipeline (ingestion → pricing → scoring → rules → alerts). No parallel execution needed at 5-15 min intervals.
