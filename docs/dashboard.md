# Dashboard Pages

## Page Structure

```
frontend/src/app/
├── layout.tsx              # Sidebar nav + top bar
├── page.tsx                # Landing / redirect to /dashboard
├── globals.css
├── dashboard/page.tsx      # Overview
├── options/page.tsx        # Options chain browser
├── convexity/page.tsx      # Convexity rankings
├── scenarios/page.tsx      # Scenario analysis
├── portfolio/page.tsx      # Positions + risk
├── rules/page.tsx          # Rules management
├── alerts/page.tsx         # Alert config + history
└── settings/page.tsx       # API keys, sources, scheduler
```

## Page Details

### /dashboard — Overview

```
┌──────────────────────────────────────────────────────────┐
│  Portfolio Value    Net Delta    Net Gamma    Alerts     │
│  $125,430          +0.12        -0.03        2 active   │
├──────────────────────────────────────────────────────────┤
│  P&L Chart (line)                │  Greeks Exposure      │
│  30-day P&L over time            │  Stacked bar:         │
│  [Recharts LineChart]            │  Delta/Gamma/Theta    │
│                                  │  [Recharts BarChart]  │
├──────────────────────────────────────────────────────────┤
│  Recent Alerts                                      │
│  ┌─────────┬──────────────┬──────────┬──────────┐   │
│  │ Time    │ Rule         │ Action   │ Status   │   │
│  ├─────────┼──────────────┼──────────┼──────────┤   │
│  │ 14:30   │ convex_barg  │ buy      │ pending  │   │
│  │ 13:15   │ delta_hedge  │ rebalance│ sent     │   │
│  └─────────┴──────────────┴──────────┴──────────┘   │
└──────────────────────────────────────────────────────────┘
```

**Components:** `Dashboard.tsx`, `PnLChart.tsx`, `GreeksExposure.tsx`, `AlertHistory.tsx`

### /options — Options Chain Browser

```
┌──────────────────────────────────────────────────────────┐
│    Underlying: [AAPL ▼]  Expiration: [Feb 21 ▼]          │
├──────────────────────────────────────────────────────────┤
│   Calls                    │  Puts                       │
│  ┌──────┬─────┬─────┬────┤  ├──────┬─────┬─────┬────┐  │
│  │Bid   │Ask  │IV   │Δ   │  │Δ     │IV   │Ask  │Bid │  │
│  ├──────┼─────┼─────┼────┤  ├──────┼─────┼─────┼────┤  │
│  │2.15  │2.20 │0.32 │0.54│  │-0.46 │0.35 │3.80 │3.75│  │
│  │1.50  │1.55 │0.28 │0.42│  │-0.58 │0.31 │2.90 │2.85│  │
│  └──────┴─────┴─────┴────┘  └──────┴─────┴─────┴────┘  │
├──────────────────────────────────────────────────────────┤
│  Volatility Surface (IV by strike × expiration)          │
│  [Recharts grouped bar or heatmap]                       │
└──────────────────────────────────────────────────────────┘
```

**Components:** `OptionsChain.tsx`, `VolSurface.tsx`

### /convexity — Convexity Rankings

```
┌──────────────────────────────────────────────────────────┐
│   Filters: Min Score [70] Max IV Rank [50] Min Vol [100] │
├──────────────────────────────────────────────────────────┤
│   Convexity Scatter: Gamma/Theta vs IV Percentile        │
│   [Recharts ScatterChart]                                │
├──────────────────────────────────────────────────────────┤
│  Ranked Table                                            │
│  ┌────┬──────────┬───────┬─────┬──────┬───────┐          │
│  │Rank│Contract  │Score  │Γ/Θ  │IV Rank│Action │         │
│  ├────┼──────────┼───────┼─────┼──────┼───────┤          │
│  │ 1  │AAPL 190C │82.5   │4.2  │35    │[Buy]  │          │
│  │ 2  │SPX 5100P │78.1   │3.8  │42    │[Buy]  │          │
│  │ 3  │TSLA 250C │75.3   │3.5  │28    │[Buy]  │          │
│  └────┴──────────┴───────┴─────┴──────┴───────┘          │
└──────────────────────────────────────────────────────────┘
```

**Components:** `ConvexityRankings.tsx`

### /scenarios — Scenario Analysis

```
┌──────────────────────────────────────────────────────────┐
│  Scenario: [Price Shock ▼]  Run on: [Portfolio ▼]       │
├──────────────────────────────────────────────────────────┤
│  Parameters                                              │
│  Price shocks: [-20%, -10%, -5%, 0%, +5%, +10%, +20%]  │
│  Vol shocks:   [-10%, -5%, 0%, +5%, +10%]              │
├──────────────────────────────────────────────────────────┤
│  Results                                                 │
│  P&L Impact by Price Shock                              │
│  [Recharts BarChart — grouped by vol shock]             │
├──────────────────────────────────────────────────────────┤
│  Detailed Table                                          │
│  ┌────────┬────────┬────────┬────────┬────────┐     │
│  │Price Δ │Vol Δ   │P&L     │Δ Impact│Γ Impact│     │
│  ├────────┼────────┼────────┼────────┼────────┤     │
│  │-10%    │+5%     │-$3,200 │-0.12   │+0.01  │     │
│  └────────┴────────┴────────┴────────┴────────┘     │
└──────────────────────────────────────────────────────────┘
```

**Components:** `ScenarioRunner.tsx`

### /portfolio — Positions + Risk

```
┌──────────────────────────────────────────────────────────┐
│  Portfolio: [Main ▼]  Budget: $100,000  Used: $45,000  │
├──────────────────────────────────────────────────────────┤
│  Positions                                               │
│  ┌──────────┬─────┬───────┬───────┬────────┬──────┐   │
│  │Contract  │Qty  │Entry  │Current│P&L     │Δ     │   │
│  ├──────────┼─────┼───────┼───────┼────────┼──────┤   │
│  │AAPL 190C │+10  │$2.15  │$2.80  │+$650   │+0.54 │   │
│  │SPX 5100P │-5   │$3.80  │$3.20  │+$300   │-0.23 │   │
│  └──────────┴─────┴───────┴───────┴────────┴──────┘   │
├──────────────────────────────────────────────────────────┤
│  Portfolio Greeks                                         │
│  Net Δ: +0.31  Net Γ: -0.02  Net Θ: -$45  Net ν: +1.2│
│  [Greeks gauge components]                               │
├──────────────────────────────────────────────────────────┤
│  Risk Limits                                              │
│  ┌──────────────┬──────────┬──────────┬──────┐       │
│  │Metric        │Current   │Limit     │Status│       │
│  ├──────────────┼──────────┼──────────┼──────┤       │
│  │|Net Delta|   │0.31      │0.50      │  OK  │       │
│  │Max Position  │$6,500    │$10,000   │  OK  │       │
│  └──────────────┴──────────┴──────────┴──────┘       │
└──────────────────────────────────────────────────────────┘
```

**Components:** `PositionsTable.tsx`, `RiskLimits.tsx`

### /rules — Rules Management

```
┌──────────────────────────────────────────────────────────┐
│  Active Rules                                     [Add] │
├──────────────────────────────────────────────────────────┤
│  ┌──────────────────┬──────┬──────────┬──────────────┐  │
│  │Rule              │Status│Priority  │Last Triggered│  │
│  ├──────────────────┼──────┼──────────┼──────────────┤  │
│  │delta_hedge       │  ON  │    5     │ 2h ago       │  │
│  │convexity_bargain │  ON  │   10     │ 45m ago      │  │
│  │vol_skew          │ OFF  │   15     │ 3d ago       │  │
│  └──────────────────┴──────┴──────────┴──────────────┘  │
├──────────────────────────────────────────────────────────┤
│  Trigger History                                         │
│  ┌─────────┬──────────────┬──────────┬──────────────┐  │
│  │Time     │Rule          │Action    │Details       │  │
│  ├─────────┼──────────────┼──────────┼──────────────┤  │
│  │14:30    │convex_barg   │buy       │AAPL 190C x5 │  │
│  │13:15    │delta_hedge   │rebalance │Net Δ > 0.15 │  │
│  └─────────┴──────────────┴──────────┴──────────────┘  │
└──────────────────────────────────────────────────────────┘
```

**Components:** `RulesList.tsx`, `TriggerHistory.tsx`

### /alerts — Alert Config

```
┌──────────────────────────────────────────────────────────┐
│  Channels                                       [Add]   │
├──────────────────────────────────────────────────────────┤
│  ┌────────────┬──────────┬──────────┬──────────────┐   │
│  │Channel     │Type      │Status    │Subscriptions │   │
│  ├────────────┼──────────┼──────────┼──────────────┤   │
│  │Slack       │webhook   │  ON      │3 rules       │   │
│  │Email       │email     │  ON      │5 rules       │   │
│  └────────────┴──────────┴──────────┴──────────────┘   │
├──────────────────────────────────────────────────────────┤
│  Recent Alerts                                           │
│  ┌─────────┬──────────┬────────────┬────────────────┐  │
│  │Time     │Channel   │Subject     │Status          │  │
│  ├─────────┼──────────┼────────────┼────────────────┤  │
│  │14:30    │Slack     │Convexity...│ sent           │  │
│  │13:15    │Email     │Delta hedg..│ sent           │  │
│  └─────────┴──────────┴────────────┴────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

**Components:** `AlertHistory.tsx`, `ChannelConfig.tsx`

### /settings — Configuration

```
┌──────────────────────────────────────────────────────────┐
│  API Keys                                                │
│  Polygon.io: [••••••••] [Test] [Save]                   │
│  IBKR:       [Connected] [Gateway: localhost:4002]       │
├──────────────────────────────────────────────────────────┤
│  Scheduler Status                                        │
│  Pipeline: Running (every 5 min)                         │
│  Last run: 14:30 — 2.3s — 847 contracts updated         │
│  Next run: 14:35                                         │
├──────────────────────────────────────────────────────────┤
│  Data Sources                                            │
│  ┌──────────┬──────────┬──────────┬──────────────┐     │
│  │Source    │Status    │Freshness │Last Fetch     │     │
│  ├──────────┼──────────┼──────────┼──────────────┤     │
│  │Polygon   │active    │2m ago    │14:28          │     │
│  │IBKR      │active    │3m ago    │14:27          │     │
│  │Yahoo     │active    │8m ago    │14:22          │     │
│  │CBOE      │active    │6h ago    │08:30          │     │
│  └──────────┴──────────┴──────────┴──────────────┘     │
└──────────────────────────────────────────────────────────┘
```

**Components:** `SchedulerStatus.tsx`, `DataSourceStatus.tsx`

## Recharts Components

| Component          | Chart Type         | Data                                   |
| ------------------ | ------------------ | -------------------------------------- |
| `PnLChart`         | LineChart          | Daily P&L over 30 days                 |
| `GreeksExposure`   | BarChart (stacked) | Net delta/gamma/theta/vega by position |
| `VolSurface`       | BarChart (grouped) | IV by strike × expiration              |
| `ConvexityScatter` | ScatterChart       | Gamma/Theta ratio vs IV percentile     |
| `ScenarioResults`  | BarChart (grouped) | P&L under price × vol shocks           |
| `AlertTimeline`    | BarChart           | Alerts triggered per day               |
