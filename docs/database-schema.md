# Database Schema

PostgreSQL 16 with TimescaleDB extension for time-series optimization.

## Reference Data

### tickers

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| symbol | VARCHAR(20) UNIQUE | Ticker symbol (AAPL, SPX, VIX) |
| name | VARCHAR(255) | Company/index name |
| type | VARCHAR(20) | equity, index, etf |
| exchange | VARCHAR(20) | NYSE, NASDAQ, CBOE |
| sector | VARCHAR(100) | Sector (equities only) |
| active | BOOLEAN | Currently tradeable |
| created_at | TIMESTAMPTZ | Row creation time |
| updated_at | TIMESTAMPTZ | Last update |

### options_contracts

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| ticker_id | UUID FK→tickers | Underlying ticker |
| occ_symbol | VARCHAR(30) UNIQUE | OCC standard symbol |
| expiration_date | DATE | Expiration date |
| strike | NUMERIC(12,4) | Strike price |
| option_type | VARCHAR(4) | call, put |
| multiplier | INT | Contract multiplier (100) |
| active | BOOLEAN | Currently tradeable |
| created_at | TIMESTAMPTZ | Row creation time |

**Indexes:**
- `idx_contracts_ticker_exp` on (ticker_id, expiration_date)
- `idx_contracts_strike_type` on (ticker_id, strike, option_type)

## Market Data

### underlying_bars

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| ticker_id | UUID FK→tickers | Underlying ticker |
| timestamp | TIMESTAMPTZ | Bar open time |
| interval | VARCHAR(5) | 1m, 5m, 15m, 1h, 1d |
| open | NUMERIC(12,4) | Open price |
| high | NUMERIC(12,4) | High price |
| low | NUMERIC(12,4) | Low price |
| close | NUMERIC(12,4) | Close price |
| volume | BIGINT | Volume |
| created_at | TIMESTAMPTZ | Row creation time |

**Indexes:**
- `idx_underlying_bars_lookup` on (ticker_id, interval, timestamp DESC)

### options_bars

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| contract_id | UUID FK→options_contracts | Option contract |
| timestamp | TIMESTAMPTZ | Bar open time |
| interval | VARCHAR(5) | 1m, 5m, 15m, 1h, 1d |
| open | NUMERIC(12,4) | Open price |
| high | NUMERIC(12,4) | High price |
| low | NUMERIC(12,4) | Low price |
| close | NUMERIC(12,4) | Close price |
| volume | BIGINT | Volume |
| open_interest | BIGINT | Open interest |
| created_at | TIMESTAMPTZ | Row creation time |

### options_snapshots

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| contract_id | UUID FK→options_contracts | Option contract |
| timestamp | TIMESTAMPTZ | Snapshot time |
| bid | NUMERIC(12,4) | Best bid |
| ask | NUMERIC(12,4) | Best ask |
| last | NUMERIC(12,4) | Last trade price |
| volume | BIGINT | Daily volume |
| open_interest | BIGINT | Open interest |
| implied_volatility | NUMERIC(8,6) | Implied volatility |
| delta | NUMERIC(8,6) | Option delta |
| gamma | NUMERIC(8,6) | Option gamma |
| theta | NUMERIC(8,6) | Option theta |
| vega | NUMERIC(8,6) | Option vega |
| rho | NUMERIC(8,6) | Option rho |
| created_at | TIMESTAMPTZ | Row creation time |

**Note:** If provider returns Greeks (Polygon does), store them directly. Otherwise calculated by pricing engine.

## Volatility

### volatility_surface

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| ticker_id | UUID FK→tickers | Underlying ticker |
| date | DATE | Surface date |
| expiration_date | DATE | Expiration date |
| strike | NUMERIC(12,4) | Strike price |
| iv | NUMERIC(8,6) | Implied volatility |
| created_at | TIMESTAMPTZ | Row creation time |

**Indexes:**
- `idx_vol_surface_lookup` on (ticker_id, date, expiration_date)

### historical_volatility

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| ticker_id | UUID FK→tickers | Underlying ticker |
| date | DATE | Calculation date |
| hv_20 | NUMERIC(8,6) | 20-day HV |
| hv_30 | NUMERIC(8,6) | 30-day HV |
| hv_60 | NUMERIC(8,6) | 60-day HV |
| hv_90 | NUMERIC(8,6) | 90-day HV |
| created_at | TIMESTAMPTZ | Row creation time |

## Scenarios

### scenario_templates

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| name | VARCHAR(100) UNIQUE | Template name |
| description | TEXT | Human description |
| parameters | JSONB | Scenario params (see below) |
| active | BOOLEAN | Currently running |
| created_at | TIMESTAMPTZ | Row creation time |
| updated_at | TIMESTAMPTZ | Last update |

**parameters JSONB structure:**
```json
{
  "type": "price_shock",
  "shocks": [-0.20, -0.10, -0.05, 0, 0.05, 0.10, 0.20],
  "vol_shocks": [-0.10, -0.05, 0, 0.05, 0.10],
  "time_decay_days": [1, 7, 14, 30]
}
```

### scenario_runs

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| template_id | UUID FK→scenario_templates | Template used |
| portfolio_id | UUID FK→portfolios | Target portfolio |
| status | VARCHAR(20) | pending, running, complete, failed |
| results | JSONB | Scenario results |
| started_at | TIMESTAMPTZ | Start time |
| completed_at | TIMESTAMPTZ | End time |
| created_at | TIMESTAMPTZ | Row creation time |

## Convexity

### convexity_scores

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| contract_id | UUID FK→options_contracts | Option contract |
| date | DATE | Score date |
| score | NUMERIC(8,4) | Composite convexity score (0-100) |
| gamma_per_theta | NUMERIC(8,6) | Gamma / abs(theta) ratio |
| vega_normalized | NUMERIC(8,6) | Vega normalized by price |
| iv_rank | NUMERIC(8,4) | IV rank (0-100) |
| iv_percentile | NUMERIC(8,4) | IV percentile (0-100) |
| created_at | TIMESTAMPTZ | Row creation time |

**Indexes:**
- `idx_convexity_rank` on (date, score DESC) — for ranking queries
- `idx_convexity_contract_date` on (contract_id, date)

## Portfolio

### portfolios

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| name | VARCHAR(100) | Portfolio name |
| description | TEXT | Description |
| budget | NUMERIC(14,2) | Capital budget |
| created_at | TIMESTAMPTZ | Row creation time |
| updated_at | TIMESTAMPTZ | Last update |

### positions

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| portfolio_id | UUID FK→portfolios | Parent portfolio |
| contract_id | UUID FK→options_contracts | Option contract |
| quantity | INT | Signed quantity (long positive) |
| entry_price | NUMERIC(12,4) | Entry price per contract |
| entry_date | DATE | Entry date |
| current_price | NUMERIC(12,4) | Current market price |
| unrealized_pnl | NUMERIC(14,2) | Current unrealized P&L |
| created_at | TIMESTAMPTZ | Row creation time |
| updated_at | TIMESTAMPTZ | Last update |

### portfolio_greeks

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| portfolio_id | UUID FK→portfolios | Parent portfolio |
| timestamp | TIMESTAMPTZ | Calculation time |
| net_delta | NUMERIC(14,4) | Sum of (delta × qty × multiplier) |
| net_gamma | NUMERIC(14,6) | Sum of (gamma × qty × multiplier) |
| net_theta | NUMERIC(14,4) | Sum of (theta × qty × multiplier) |
| net_vega | NUMERIC(14,4) | Sum of (vega × qty × multiplier) |
| created_at | TIMESTAMPTZ | Row creation time |

## Rules

### rule_definitions

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| name | VARCHAR(100) UNIQUE | Rule name |
| rule_type | VARCHAR(20) | code, yaml, hybrid |
| module_path | VARCHAR(255) | Python module path (for code rules) |
| config | JSONB | Strategy parameters (YAML-loaded) |
| active | BOOLEAN | Currently evaluated |
| priority | INT | Evaluation order (lower = first) |
| created_at | TIMESTAMPTZ | Row creation time |
| updated_at | TIMESTAMPTZ | Last update |

### rule_triggers

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| rule_id | UUID FK→rule_definitions | Triggered rule |
| triggered_at | TIMESTAMPTZ | Trigger time |
| context | JSONB | Market/portfolio snapshot at trigger |
| action_taken | VARCHAR(50) | buy, sell, alert, rebalance |
| created_at | TIMESTAMPTZ | Row creation time |

### rule_audit_log

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| rule_id | UUID FK→rule_definitions | Related rule |
| action | VARCHAR(50) | triggered, dismissed, modified, enabled, disabled |
| details | JSONB | Action details |
| created_at | TIMESTAMPTZ | Row creation time |

## Alerts

### alert_channels

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| name | VARCHAR(100) | Channel name |
| type | VARCHAR(20) | email, webhook |
| config | JSONB | Channel-specific config |
| active | BOOLEAN | Currently sending |
| created_at | TIMESTAMPTZ | Row creation time |

**email config:**
```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "username": "...",
  "password": "...",
  "from_addr": "...",
  "to_addrs": ["..."]
}
```

**webhook config:**
```json
{
  "url": "https://hooks.slack.com/...",
  "method": "POST",
  "headers": { "Content-Type": "application/json" }
}
```

### alert_subscriptions

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| channel_id | UUID FK→alert_channels | Alert channel |
| rule_id | UUID FK→rule_definitions | Triggering rule |
| active | BOOLEAN | Subscription active |
| created_at | TIMESTAMPTZ | Row creation time |

### alert_history

| Column | Type | Description |
|---|---|---|
| id | UUID PK | Auto-generated |
| channel_id | UUID FK→alert_channels | Channel used |
| rule_id | UUID FK→rule_definitions | Triggering rule |
| subject | VARCHAR(255) | Alert subject line |
| body | TEXT | Alert body |
| status | VARCHAR(20) | sent, failed, pending |
| sent_at | TIMESTAMPTZ | Send time |
| created_at | TIMESTAMPTZ | Row creation time |
