# Dependencies

## Backend (Python 3.12)

### Core
| Package | Version | Purpose |
|---|---|---|
| fastapi | 0.115.6 | Web framework |
| uvicorn[standard] | 0.34.0 | ASGI server |
| sqlalchemy[asyncio] | 2.0.36 | ORM + async DB |
| alembic | 1.14.1 | Database migrations |
| asyncpg | 0.30.0 | PostgreSQL async driver |
| pydantic-settings | 2.7.1 | Configuration management |
| python-dotenv | 1.0.1 | .env file loading |

### Data Sources
| Package | Version | Purpose |
|---|---|---|
| polygon-api-client | 1.14.0 | Polygon.io REST API |
| ib_async | 1.0.2 | Interactive Brokers TWS/Gateway API |
| yfinance | 0.2.50 | Yahoo Finance data |
| requests | 2.32.3 | HTTP client for CBOE scraping |

### Pricing
| Package | Version | Purpose |
|---|---|---|
| vollib | 1.0.7 | Black-Scholes Greeks + IV calculation |

### Scheduling
| Package | Version | Purpose |
|---|---|---|
| apscheduler | 3.10.4 | In-process job scheduler |

### Alerts
| Package | Version | Purpose |
|---|---|---|
| aiosmtplib | 3.0.2 | Async email sending (SMTP) |
| httpx | 0.28.1 | Async HTTP client (webhooks) |

### Config
| Package | Version | Purpose |
|---|---|---|
| pyyaml | 6.0.2 | YAML strategy config files |

## Frontend (Node.js 20)

### Core
| Package | Version | Purpose |
|---|---|---|
| next | 15.1.x | React framework (App Router) |
| react | 19.x | UI library |
| react-dom | 19.x | React DOM |

### Visualization
| Package | Version | Purpose |
|---|---|---|
| recharts | 2.15.x | Chart library (built on D3) |

### Dev
| Package | Version | Purpose |
|---|---|---|
| typescript | 5.7.x | Type checking |
| @types/node | 22.x | Node.js types |
| @types/react | 19.x | React types |
| @types/react-dom | 19.x | ReactDOM types |

## Infrastructure

| Service | Version | Purpose |
|---|---|---|
| PostgreSQL | 16-alpine | Primary database |
| TimescaleDB | latest-pg16 | Time-series extension (drop-in PG) |
| Node.js | 20-alpine | Frontend build/run |
| Python | 3.12-slim | Backend runtime |

## requirements.txt (consolidated)

```
# Core
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
alembic==1.14.1
asyncpg==0.30.0
pydantic-settings==2.7.1
python-dotenv==1.0.1

# Data Sources
polygon-api-client==1.14.0
ib_async==1.0.2
yfinance==0.2.50
requests==2.32.3

# Pricing
vollib==1.0.7

# Scheduling
apscheduler==3.10.4

# Alerts
aiosmtplib==3.0.2
httpx==0.28.1

# Config
pyyaml==6.0.2
```
