# Module Breakdown

## Module Structure

Each module follows the same pattern:

```
modules/<name>/
├── __init__.py
├── models.py       # SQLAlchemy ORM models
├── schemas.py      # Pydantic request/response schemas
├── service.py      # Business logic (imported by other modules)
├── router.py       # FastAPI router (API endpoints)
└── engine.py       # (optional) Heavy computation logic
```

Rules:
- `models.py` defines tables; `schemas.py` defines API contracts
- `service.py` is the public interface — other modules call service functions
- `router.py` maps HTTP endpoints to service functions
- No circular imports between modules

---

## Module: `data_sources`

**Purpose:** Adapter layer for multiple market data providers.

| File | Responsibility |
|---|---|
| `base.py` | `BaseDataAdapter` ABC with standard interface |
| `polygon.py` | Polygon.io REST adapter (snapshots, chains, Greeks) |
| `ibkr.py` | Interactive Brokers adapter via ib_async |
| `yahoo.py` | Yahoo Finance adapter via yfinance |
| `cboe.py` | CBOE data adapter |
| `router.py` | Source status, manual trigger endpoints |

**Public interface:**
```python
# base.py
class BaseDataAdapter(ABC):
    @abstractmethod
    async def fetch_options_chain(self, symbol: str) -> list[OptionContract]: ...

    @abstractmethod
    async def fetch_snapshot(self, symbol: str) -> list[OptionSnapshot]: ...

    @abstractmethod
    async def fetch_underlying(self, symbol: str) -> UnderlyingBar: ...
```

---

## Module: `ingestion`

**Purpose:** Scheduled fetching, normalization, deduplication, freshness tracking.

| File | Responsibility |
|---|---|
| `models.py` | Ingestion jobs table (status, timestamps, errors) |
| `service.py` | `run_ingestion()`, `normalize()`, `upsert_contracts()` |
| `router.py` | Job status, manual trigger endpoints |

**Key functions:**
```python
async def run_ingestion(db: AsyncSession) -> IngestionResult:
    """Full ingestion cycle: fetch all sources → normalize → upsert."""

async def normalize(raw_data: list[dict], source: str) -> list[NormalizedOption]:
    """Normalize provider-specific format to common schema."""
```

---

## Module: `options_data`

**Purpose:** Core data models, queries, and access patterns for options data.

| File | Responsibility |
|---|---|
| `models.py` | Tickers, contracts, bars, snapshots, vol_surface, hv |
| `schemas.py` | Request/response for options queries |
| `service.py` | `get_chain()`, `get_snapshot()`, `get_vol_surface()` |

**Key functions:**
```python
async def get_options_chain(db, symbol: str, expiration: date | None) -> list[OptionContract]: ...
async def get_latest_snapshot(db, contract_id: UUID) -> OptionSnapshot | None: ...
async def get_vol_surface(db, symbol: str, date: date) -> VolatilitySurface: ...
```

---

## Module: `pricing`

**Purpose:** Black-Scholes Greeks calculation, IV surface construction, theoretical pricing.

| File | Responsibility |
|---|---|
| `engine.py` | vollib wrapper — `calculate_greeks()`, `calculate_iv()` |
| `vol_surface.py` | IV surface interpolation and visualization data |
| `models.py` | Greeks snapshots table (calculated vs provider) |
| `router.py` | Pricing endpoints |

**Key functions:**
```python
def calculate_greeks(
    spot: float, strike: float, rate: float,
    time_to_expiry: float, iv: float, option_type: str
) -> Greeks: ...

def calculate_iv(
    market_price: float, spot: float, strike: float,
    rate: float, time_to_expiry: float, option_type: str
) -> float: ...

async def build_vol_surface(db, symbol: str, date: date) -> VolSurfaceData: ...
```

---

## Module: `scenarios`

**Purpose:** Stress testing, what-if analysis, Monte Carlo simulation.

| File | Responsibility |
|---|---|
| `engine.py` | Scenario runners — price shock, vol shock, time decay, MC |
| `models.py` | scenario_templates, scenario_runs |
| `schemas.py` | Scenario config, run results |
| `router.py` | CRUD + run endpoints |

**Scenario types:**
- **Price shock:** Apply % change to underlying, recalculate portfolio P&L
- **Vol shock:** Apply IV change, recalculate Greeks and P&L
- **Time decay:** Advance time by N days, show theta impact
- **Combined:** Price + vol + time simultaneously
- **Monte Carlo:** Random paths, distribution of outcomes

---

## Module: `convexity`

**Purpose:** Score and rank options by convexity profile.

| File | Responsibility |
|---|---|
| `engine.py` | `score_options()`, `rank_by_convexity()` |
| `models.py` | convexity_scores table |
| `router.py` | Ranking endpoints |

**Scoring formula (composite 0-100):**
```python
score = weighted_sum(
    gamma_per_theta=0.30,      # Higher = cheaper convexity
    vega_normalized=0.25,       # Vol exposure per $ of premium
    iv_rank_inverse=0.20,       # Lower IV rank = better value
    volume_oi_ratio=0.15,       # Liquidity factor
    time_to_expiry_factor=0.10  # Optimal DTE window
)
```

---

## Module: `portfolio`

**Purpose:** Position tracking, Greeks aggregation, risk budget management.

| File | Responsibility |
|---|---|
| `models.py` | portfolios, positions, portfolio_greeks |
| `service.py` | `aggregate_greeks()`, `check_risk_limits()`, `size_position()` |
| `router.py` | Portfolio CRUD, position management |

**Key functions:**
```python
async def aggregate_greeks(db, portfolio_id: UUID) -> PortfolioGreeks:
    """Sum Greeks across all positions: net_delta, net_gamma, etc."""

async def check_risk_limits(db, portfolio_id: UUID) -> list[RiskViolation]:
    """Check positions against configured risk limits."""

async def size_position(
    portfolio_id: UUID, contract_id: UUID,
    risk_budget: float, max_delta: float
) -> PositionSize:
    """Calculate position size within risk constraints."""
```

---

## Module: `rules`

**Purpose:** Decision rules engine — code-based rules, YAML params, DB audit.

| File | Responsibility |
|---|---|
| `base.py` | `BaseRule` ABC, `RuleContext`, `RuleResult` |
| `registry.py` | Auto-discovers and registers code-based rules |
| `engine.py` | `evaluate_all()`, YAML loader, DB persistence |
| `rules/` | Concrete rule implementations |
| `models.py` | rule_definitions, rule_triggers, rule_audit_log |
| `router.py` | Rules CRUD, trigger history |

See [Rules Engine](rules-engine.md) for detailed design.

---

## Module: `alerts`

**Purpose:** Dispatch notifications via email and webhook.

| File | Responsibility |
|---|---|
| `channels.py` | `EmailChannel`, `WebhookChannel` implementations |
| `service.py` | `dispatch()`, subscription matching |
| `models.py` | alert_channels, alert_subscriptions, alert_history |
| `router.py` | Channel CRUD, history endpoints |

**Key functions:**
```python
async def dispatch(db, rule_trigger: RuleTrigger) -> list[AlertResult]:
    """Find subscribed channels, send alert to each."""

async def send_email(config: dict, subject: str, body: str) -> bool: ...
async def send_webhook(config: dict, payload: dict) -> bool: ...
```

---

## Module: `dashboard`

**Purpose:** Aggregated API endpoints for the frontend.

| File | Responsibility |
|---|---|
| `router.py` | Overview, summary, stats endpoints |

**Endpoints:**
```python
GET /api/dashboard/overview     # Portfolio value, total Greeks, recent alerts
GET /api/dashboard/pnl         # P&L time series
GET /api/dashboard/exposure     # Greeks breakdown by position
GET /api/dashboard/convexity    # Top convexity rankings
GET /api/dashboard/scenarios    # Latest scenario results
```
