import logging
from datetime import date, datetime, timezone

import httpx

from app.config import settings
from app.modules.data_sources.base import (
    BaseDataAdapter,
    FetchResult,
    NormalizedContract,
    NormalizedSnapshot,
    NormalizedUnderlyingBar,
    OptionType,
)

logger = logging.getLogger(__name__)


class PolygonAdapter(BaseDataAdapter):
    name = "polygon"

    def __init__(self) -> None:
        self.api_key = settings.POLYGON_API_KEY
        self.base_url = "https://api.polygon.io"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                params={"apiKey": self.api_key},
                timeout=30.0,
            )
        return self._client

    async def fetch_options_chain(self, symbol: str) -> list[NormalizedContract]:
        if not self.api_key:
            logger.warning("Polygon API key not configured")
            return []

        client = await self._get_client()
        contracts = []
        url = f"/v3/reference/options/contracts"
        params = {
            "underlying_ticker": symbol.upper(),
            "limit": 1000,
            "status": "active",
        }

        try:
            while True:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

                for contract in data.get("results", []):
                    try:
                        exp_str = contract.get("expiration_date", "")
                        exp_date = date.fromisoformat(exp_str) if exp_str else None
                        if not exp_date:
                            continue

                        strike = contract.get("strike_price", 0)
                        cpx_type = contract.get("type", "").lower()
                        opt_type = OptionType.CALL if cpx_type == "call" else OptionType.PUT
                        occ = contract.get("ticker", "")

                        contracts.append(NormalizedContract(
                            occ_symbol=occ,
                            underlying_symbol=symbol.upper(),
                            expiration_date=exp_date,
                            strike=float(strike),
                            option_type=opt_type,
                            multiplier=int(contract.get("share_multiplier", 100)),
                        ))
                    except (ValueError, KeyError) as e:
                        logger.debug(f"Skipping contract: {e}")
                        continue

                next_url = data.get("next_url")
                if not next_url:
                    break
                url = next_url
                params = {}

        except httpx.HTTPError as e:
            logger.error(f"Polygon fetch_options_chain failed: {e}")

        return contracts

    async def fetch_snapshots(self, symbol: str) -> list[NormalizedSnapshot]:
        if not self.api_key:
            return []

        client = await self._get_client()
        snapshots = []
        url = f"/v3/snapshot/options/{symbol.upper()}"

        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("results", []):
                try:
                    details = item.get("details", {})
                    greeks = item.get("greeks", {})
                    last_quote = item.get("last_quote", {})
                    last_trade = item.get("last_trade", {})
                    session = item.get("session", {})

                    occ = details.get("ticker", "")
                    if not occ:
                        continue

                    snapshots.append(NormalizedSnapshot(
                        occ_symbol=occ,
                        underlying_symbol=symbol.upper(),
                        timestamp=datetime.now(timezone.utc),
                        bid=float(last_quote.get("bid", 0)) or None,
                        ask=float(last_quote.get("ask", 0)) or None,
                        last=float(last_trade.get("price", 0)) or None,
                        volume=int(session.get("volume", 0)) or None,
                        open_interest=int(item.get("open_interest", 0)) or None,
                        implied_volatility=float(greeks.get("implied_volatility", 0)) or None,
                        delta=float(greeks.get("delta", 0)) or None,
                        gamma=float(greeks.get("gamma", 0)) or None,
                        theta=float(greeks.get("theta", 0)) or None,
                        vega=float(greeks.get("vega", 0)) or None,
                        rho=float(greeks.get("rho", 0)) or None,
                    ))
                except (ValueError, KeyError) as e:
                    logger.debug(f"Skipping snapshot: {e}")
                    continue

        except httpx.HTTPError as e:
            logger.error(f"Polygon fetch_snapshots failed: {e}")

        return snapshots

    async def fetch_underlying_bar(self, symbol: str, interval: str = "1d") -> NormalizedUnderlyingBar | None:
        if not self.api_key:
            return None

        client = await self._get_client()
        url = f"/v2/aggs/ticker/{symbol.upper()}/prev"

        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])

            if not results:
                return None

            r = results[0]
            ts_ms = r.get("t", 0)
            return NormalizedUnderlyingBar(
                symbol=symbol.upper(),
                timestamp=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
                interval=interval,
                open=float(r.get("o", 0)),
                high=float(r.get("h", 0)),
                low=float(r.get("l", 0)),
                close=float(r.get("c", 0)),
                volume=int(r.get("v", 0)),
            )

        except httpx.HTTPError as e:
            logger.error(f"Polygon fetch_underlying_bar failed: {e}")
            return None

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            client = await self._get_client()
            resp = await client.get("/v3/reference/conditions", params={"limit": 1})
            return resp.status_code == 200
        except Exception:
            return False
