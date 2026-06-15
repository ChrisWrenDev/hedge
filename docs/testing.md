# Testing Strategy

## Overview

Hedge uses a layered testing approach: fast unit tests for business logic, integration tests for database and API routes, and end-to-end tests for critical flows. External data sources are always mocked.

## Testing Pyramid

```
        ┌──────────┐
        │   E2E    │  Few — critical user flows only
        ├──────────┤
        │ Integration│  Some — DB, API routes, pipelines
        ├──────────┤
        │   Unit    │  Many — engines, services, adapters
        └──────────┘
```

## Tooling

| Tool | Purpose |
|---|---|
| pytest | Test runner |
| pytest-asyncio | Async test support |
| httpx | AsyncTestClient for FastAPI routes |
| pytest-cov | Coverage reporting |
| factory_boy | Test data factories (optional) |
| respx | Mock httpx calls for external APIs |
| yfinance stubs | Mock Yahoo Finance responses |

```txt
# tests/requirements.txt
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
httpx==0.28.1
respx==0.22.0
```

## Directory Structure

```
backend/
├── tests/
│   ├── conftest.py              # Shared fixtures (db session, test client, factories)
│   ├── unit/
│   │   ├── test_pricing_engine.py
│   │   ├── test_convexity_engine.py
│   │   ├── test_rules_engine.py
│   │   └── test_data_adapters.py
│   ├── integration/
│   │   ├── test_options_data.py
│   │   ├── test_ingestion.py
│   │   ├── test_api_routes.py
│   │   └── test_database.py
│   └── e2e/
│       ├── test_ingestion_pipeline.py
│       └── test_full_cycle.py
```

---

## Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.modules.options_data.models import Base

TEST_DB_URL = "postgresql+asyncpg://hedge:hedge@localhost:5432/hedge_test"


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

---

## Unit Tests

### Data Adapters

Mock all HTTP calls. Test normalization logic only.

```python
# tests/unit/test_data_adapters.py
import respx
import httpx
from datetime import date

from app.modules.data_sources.polygon import PolygonAdapter

@respx.mock
async def test_polygon_fetch_options_chain():
    respx.get("https://api.polygon.io/v3/reference/options/contracts").mock(
        return_value=httpx.Response(200, json={
            "results": [
                {
                    "ticker": "O:AAPL250321C00190000",
                    "underlying_ticker": "AAPL",
                    "expiration_date": "2025-03-21",
                    "strike_price": 190,
                    "type": "call",
                    "share_multiplier": 100,
                }
            ],
            "next_url": None,
        })
    )

    adapter = PolygonAdapter()
    adapter.api_key = "test-key"
    contracts = await adapter.fetch_options_chain("AAPL")

    assert len(contracts) == 1
    assert contracts[0].occ_symbol == "O:AAPL250321C00190000"
    assert contracts[0].strike == 190.0
    assert contracts[0].option_type.value == "call"
```

### Pricing Engine

Pure function tests, no DB or HTTP.

```python
# tests/unit/test_pricing_engine.py
from app.modules.pricing.engine import calculate_greeks, calculate_iv

def test_calculate_greeks_at_the_money():
    greeks = calculate_greeks(
        spot=100.0, strike=100.0, rate=0.05,
        time_to_expiry=0.25, iv=0.30, option_type="call"
    )
    assert abs(greeks.delta - 0.55) < 0.05  # ATM call delta ~0.55
    assert greeks.gamma > 0
    assert greeks.theta < 0  # theta is negative for long options
    assert greeks.vega > 0

def test_calculate_iv_roundtrip():
    from app.modules.pricing.engine import black_scholes_price
    price = black_scholes_price(100, 100, 0.05, 0.25, 0.30, "call")
    iv = calculate_iv(price, 100, 100, 0.05, 0.25, "call")
    assert abs(iv - 0.30) < 0.001
```

### Convexity Engine

```python
# tests/unit/test_convexity_engine.py
def test_convexity_score_range():
    from app.modules.convexity.engine import compute_score
    score = compute_score(
        gamma_per_theta=4.0,
        vega_normalized=0.02,
        iv_rank=35,
        volume_oi_ratio=0.15,
        dte=45,
    )
    assert 0 <= score <= 100

def test_higher_gamma_per_theta_increases_score():
    from app.modules.convexity.engine import compute_score
    low = compute_score(gamma_per_theta=1.0, vega_normalized=0.01, iv_rank=50, volume_oi_ratio=0.1, dte=30)
    high = compute_score(gamma_per_theta=5.0, vega_normalized=0.01, iv_rank=50, volume_oi_ratio=0.1, dte=30)
    assert high > low
```

### Rules Engine

```python
# tests/unit/test_rules_engine.py
from app.modules.rules.base import RuleContext, RuleResult
from app.modules.rules.rules.convexity_bargain import ConvexityBargainRule

def test_convexity_bargain_triggers_on_high_score():
    rule = ConvexityBargainRule()
    rule.config = {
        "min_convexity_score": 70,
        "max_iv_percentile": 50,
        "min_convexity_score": 70,
    }
    ctx = RuleContext(
        convexity_scores=[Mock(score=82.5, iv_percentile=35)],
        portfolio=Mock(delta_budget_remaining=0.5),
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.confidence > 0.7
```

---

## Integration Tests

### Database Operations

Test actual DB queries with a test database.

```python
# tests/integration/test_options_data.py
import pytest
from datetime import date

from app.modules.options_data.models import Ticker, OptionsContract
from app.modules.options_data.service import (
    get_or_create_ticker,
    get_options_chain,
    get_ticker_by_symbol,
)

@pytest.mark.asyncio
async def test_create_and_retrieve_ticker(db_session):
    ticker = await get_or_create_ticker(db_session, "AAPL", "equity", "Apple Inc.")
    await db_session.commit()

    result = await get_ticker_by_symbol(db_session, "AAPL")
    assert result is not None
    assert result.symbol == "AAPL"
    assert result.type == "equity"

@pytest.mark.asyncio
async def test_get_options_chain_filters_by_type(db_session):
    ticker = await get_or_create_ticker(db_session, "AAPL", "equity")
    db_session.add(OptionsContract(
        ticker_id=ticker.id, occ_symbol="AAPL250321C00190000",
        expiration_date=date(2025, 3, 21), strike=190, option_type="call",
    ))
    db_session.add(OptionsContract(
        ticker_id=ticker.id, occ_symbol="AAPL250321P00190000",
        expiration_date=date(2025, 3, 21), strike=190, option_type="put",
    ))
    await db_session.commit()

    calls = await get_options_chain(db_session, "AAPL", option_type="call")
    assert all(c.option_type == "call" for c in calls)
```

### API Routes

Test request/response contracts.

```python
# tests/integration/test_api_routes.py
import pytest

@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_list_tickers_empty(client):
    resp = await client.get("/api/options/tickers")
    assert resp.status_code == 200
    assert resp.json() == []

@pytest.mark.asyncio
async def test_get_ticker_not_found(client):
    resp = await client.get("/api/options/tickers/NONEXISTENT")
    assert resp.status_code == 404
```

### Ingestion Pipeline

Mock adapters, test orchestration logic.

```python
# tests/integration/test_ingestion.py
import pytest
from unittest.mock import AsyncMock, patch

from app.modules.data_sources.base import NormalizedContract, NormalizedSnapshot, OptionType
from app.modules.ingestion.service import run_ingestion

@pytest.mark.asyncio
async def test_ingestion_upserts_contracts(db_session):
    mock_adapter = AsyncMock()
    mock_adapter.name = "test_source"
    mock_adapter.fetch_options_chain.return_value = [
        NormalizedContract(
            occ_symbol="TEST250321C100",
            underlying_symbol="TEST",
            expiration_date=date(2025, 3, 21),
            strike=100.0,
            option_type=OptionType.CALL,
        )
    ]
    mock_adapter.fetch_snapshots.return_value = []
    mock_adapter.fetch_underlying_bar.return_value = None
    mock_adapter.health_check.return_value = True

    with patch("app.modules.ingestion.service.get_all_adapters", return_value=[mock_adapter]):
        results = await run_ingestion(db_session, symbols=["TEST"])

    assert len(results) == 1
    assert results[0].contracts_upserted == 1
```

---

## End-to-End Tests

Full pipeline with real DB, mocked external APIs only.

```python
# tests/e2e/test_ingestion_pipeline.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_full_ingestion_cycle(client, db_session):
    # Mock all external adapters
    mock_polygon = AsyncMock()
    mock_polygon.name = "polygon"
    mock_polygon.fetch_options_chain.return_value = [...]
    mock_polygon.fetch_snapshots.return_value = [...]
    mock_polygon.fetch_underlying_bar.return_value = None

    with patch("app.modules.ingestion.service.get_all_adapters", return_value=[mock_polygon]):
        resp = await client.post("/api/ingestion/run", json={
            "symbols": ["AAPL"],
            "sources": ["polygon"],
        })

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["contracts_upserted"] > 0

    # Verify data persisted
    resp = await client.get("/api/options/tickers")
    tickers = resp.json()
    assert any(t["symbol"] == "AAPL" for t in tickers)
```

---

## Mocking Strategy

| What | How |
|---|---|
| Polygon.io API | `respx.mock` — intercept httpx requests |
| IBKR connection | `unittest.mock.AsyncMock` — mock `ib_async.IB` |
| Yahoo Finance | `unittest.mock.patch` — mock `yfinance.Ticker` |
| CBOE scraping | `respx.mock` — intercept httpx requests |
| APScheduler | Don't mock — test `pipeline.run_full_cycle()` directly |
| Database | Use test DB, create/drop tables per test session |

---

## Running Tests

```bash
# Run all tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run specific test
pytest tests/unit/test_pricing_engine.py::test_calculate_greeks_at_the_money -v

# Run with test database
DATABASE_URL=postgresql+asyncpg://hedge:hedge@localhost:5432/hedge_test pytest
```

---

## Test Database Setup

```bash
# Create test database (one-time)
createdb hedge_test

# Or via Docker
docker compose exec db psql -U postgres -c "CREATE DATABASE hedge_test;"
```

---

## CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: hedge
          POSTGRES_PASSWORD: hedge
          POSTGRES_DB: hedge_test
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt -r tests/requirements.txt
      - run: pytest --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql+asyncpg://hedge:hedge@localhost:5432/hedge_test
      - uses: codecov/codecov-action@v4
```

---

## What to Test Per Module

| Module | Unit | Integration | E2E |
|---|---|---|---|
| data_sources | Adapter normalization, OCC parsing | Health check endpoint | — |
| options_data | — | CRUD queries, chain filtering | Chain via API |
| ingestion | — | Upsert logic, dedup | Full ingestion cycle |
| pricing | Greeks calc, IV roundtrip | — | — |
| convexity | Score formula, ranking | — | — |
| scenarios | P&L calculation | — | — |
| rules | Rule evaluation, YAML loading | Rule trigger logging | Rule → alert flow |
| alerts | Email/webhook formatting | Dispatch to channel | Rule → alert end-to-end |
| portfolio | Greeks aggregation | Position CRUD | Portfolio with positions |
