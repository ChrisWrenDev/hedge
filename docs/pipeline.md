# Pipeline Orchestration

## Overview

APScheduler runs the full analysis pipeline every 5 minutes during market hours. Each run executes all stages sequentially within a single database transaction where possible.

## Pipeline Stages

```
┌─────────────┐
│  Stage 1    │  INGESTION
│  Fetch +    │  Fetch from all data sources
│  Normalize  │  Normalize to common schema
│  Upsert     │  Upsert into options_data tables
└──────┬──────┘
       ▼
┌─────────────┐
│  Stage 2    │  PRICING
│  Greeks +   │  Calculate Greeks via vollib
│  IV Surface │  Build/update IV surface
└──────┬──────┘
       ▼
┌─────────────┐
│  Stage 3    │  SCENARIOS
│  Stress     │  Run active scenario templates
│  Tests      │  Store results
└──────┬──────┘
       ▼
┌─────────────┐
│  Stage 4    │  CONVEXITY
│  Score +    │  Score all liquid options
│  Rank       │  Update rankings
└──────┬──────┘
       ▼
┌─────────────┐
│  Stage 5    │  PORTFOLIO
│  Aggregate  │  Recalculate portfolio Greeks
│  Greeks     │  Check risk limits
└──────┬──────┘
       ▼
┌─────────────┐
│  Stage 6    │  RULES
│  Evaluate   │  Run all active rules
│  Rules      │  Log triggers
└──────┬──────┘
       ▼
┌─────────────┐
│  Stage 7    │  ALERTS
│  Dispatch   │  Send triggered alerts
│  Notify     │  Log delivery
└─────────────┘
```

## Scheduler Configuration

```python
# app/main.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

# Run every 5 minutes, Mon-Fri, 9:30-16:00 ET
scheduler.add_job(
    pipeline.run_full_cycle,
    CronTrigger(
        day_of_week='mon-fri',
        hour='9-15',
        minute='*/5',
        timezone='US/Eastern',
    ),
    id='pipeline_5min',
    coalesce=True,           # Skip if previous run still going
    max_instances=1,         # Only one pipeline at a time
    misfire_grace_time=60,   # Allow 60s late execution
)
```

## Pipeline Implementation

```python
# app/pipeline.py
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session

logger = logging.getLogger(__name__)

async def run_full_cycle():
    """Execute the full analysis pipeline."""
    async with async_session() as db:
        try:
            result = IngestionResult()

            # Stage 1: Ingestion
            logger.info("Stage 1: Ingestion")
            result = await ingestion_service.run_ingestion(db)

            # Stage 2: Pricing
            logger.info("Stage 2: Pricing")
            await pricing_service.calculate_all_greeks(db, result.updated_contracts)

            # Stage 3: Scenarios
            logger.info("Stage 3: Scenarios")
            await scenario_service.run_active_scenarios(db)

            # Stage 4: Convexity
            logger.info("Stage 4: Convexity")
            await convexity_service.score_all(db, result.updated_contracts)

            # Stage 5: Portfolio
            logger.info("Stage 5: Portfolio")
            await portfolio_service.aggregate_all(db)

            # Stage 6: Rules
            logger.info("Stage 6: Rules")
            triggers = await rules_service.evaluate_all(db)

            # Stage 7: Alerts
            if triggers:
                logger.info("Stage 7: Alerts")
                await alerts_service.dispatch_all(db, triggers)

            await db.commit()
            logger.info(f"Pipeline complete. {len(triggers)} rules triggered.")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            await db.rollback()
            raise
```

## Data Freshness

The pipeline tracks freshness per data source:

| Source | Expected Frequency | Staleness Threshold |
|---|---|---|
| Polygon.io | Real-time / 5 min | 10 min |
| IBKR | Real-time / 5 min | 10 min |
| Yahoo Finance | 15 min delayed | 30 min |
| CBOE | End of day | 24 hours |

If a source is stale beyond threshold, pricing and scoring use last-known data with a staleness flag.

## Error Handling

- **Source failure:** Continue pipeline with remaining sources. Log warning.
- **Pricing failure:** Skip Greeks calculation for affected contracts. Use provider Greeks if available.
- **Rule failure:** Log error, continue to next rule. Never block pipeline.
- **Alert failure:** Retry once after 60s. Log failure to alert_history.
- **Database failure:** Rollback entire pipeline run. Retry on next scheduled tick.

## Manual Triggers

```python
# API endpoint for manual pipeline run
@router.post("/trigger")
async def trigger_pipeline():
    """Manually trigger a full pipeline cycle."""
    job = scheduler.get_job('pipeline_5min')
    job.modify(next_run_time=datetime.now())
    return {"status": "triggered"}
```

## Monitoring

Each pipeline run logs:
- Start/end timestamp
- Per-stage duration
- Records ingested/updated per source
- Contracts priced
- Rules evaluated + triggered count
- Alerts sent/failed

Stored in `pipeline_runs` table for dashboard visibility.
