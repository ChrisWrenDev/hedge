import logging
import re
from datetime import date, datetime, timezone

import httpx

from app.modules.data_sources.base import (
    BaseDataAdapter,
    NormalizedContract,
    NormalizedSnapshot,
    NormalizedUnderlyingBar,
    OptionType,
)

logger = logging.getLogger(__name__)


class CBOEAdapter(BaseDataAdapter):
    name = "cboe"

    def __init__(self) -> None:
        self.base_url = "https://www.cboe.com/delayed_quotes"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; HedgeBot/1.0)",
                },
            )
        return self._client

    async def fetch_options_chain(self, symbol: str) -> list[NormalizedContract]:
        client = await self._get_client()
        contracts = []

        try:
            url = f"{self.base_url}/{symbol.upper()}/table"
            resp = await client.get(url)
            resp.raise_for_status()

            data = resp.json()
            quotes = data.get("quoteTable", {}).get("data", [])

            for row in quotes:
                try:
                    occ = row.get("optionName", "")
                    if not occ:
                        continue

                    parsed = _parse_occ(occ)
                    if parsed:
                        exp_date, strike, opt_type = parsed
                        contracts.append(NormalizedContract(
                            occ_symbol=occ,
                            underlying_symbol=symbol.upper(),
                            expiration_date=exp_date,
                            strike=strike,
                            option_type=opt_type,
                        ))
                except (ValueError, KeyError):
                    continue

        except httpx.HTTPError as e:
            logger.error(f"CBOE fetch_options_chain failed: {e}")
        except Exception as e:
            logger.error(f"CBOE fetch_options_chain unexpected error: {e}")

        return contracts

    async def fetch_snapshots(self, symbol: str) -> list[NormalizedSnapshot]:
        client = await self._get_client()
        snapshots = []

        try:
            url = f"{self.base_url}/{symbol.upper()}/table"
            resp = await client.get(url)
            resp.raise_for_status()

            data = resp.json()
            quotes = data.get("quoteTable", {}).get("data", [])
            now = datetime.now(timezone.utc)

            for row in quotes:
                try:
                    occ = row.get("optionName", "")
                    if not occ:
                        continue

                    parsed = _parse_occ(occ)
                    if not parsed:
                        continue

                    exp_date, strike, opt_type = parsed

                    snapshots.append(NormalizedSnapshot(
                        occ_symbol=occ,
                        underlying_symbol=symbol.upper(),
                        timestamp=now,
                        bid=_safe_float(row.get("bid")),
                        ask=_safe_float(row.get("ask")),
                        last=_safe_float(row.get("last")),
                        volume=_safe_int(row.get("volume")),
                        open_interest=_safe_int(row.get("openInterest")),
                    ))
                except (ValueError, KeyError):
                    continue

        except httpx.HTTPError as e:
            logger.error(f"CBOE fetch_snapshots failed: {e}")

        return snapshots

    async def fetch_underlying_bar(self, symbol: str, interval: str = "1d") -> NormalizedUnderlyingBar | None:
        client = await self._get_client()

        try:
            url = f"{self.base_url}/{symbol.upper()}/table"
            resp = await client.get(url)
            resp.raise_for_status()

            data = resp.json()
            quote = data.get("quoteData", {})

            if quote:
                return NormalizedUnderlyingBar(
                    symbol=symbol.upper(),
                    timestamp=datetime.now(timezone.utc),
                    interval=interval,
                    open=float(quote.get("open", 0)),
                    high=float(quote.get("high", 0)),
                    low=float(quote.get("low", 0)),
                    close=float(quote.get("last", 0)),
                    volume=int(quote.get("volume", 0)),
                )

        except Exception as e:
            logger.error(f"CBOE fetch_underlying_bar failed: {e}")

        return None

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.base_url}/SPY/table")
            return resp.status_code == 200
        except Exception:
            return False


def _parse_occ(occ: str) -> tuple[date, float, OptionType] | None:
    """Parse OCC symbol like 'SPY 2025-03-21 580.00 C' into components."""
    match = re.match(
        r"(\w+)\s+(\d{4}-\d{2}-\d{2})\s+([\d.]+)\s+([CP])",
        occ,
        re.IGNORECASE,
    )
    if not match:
        return None

    try:
        exp_date = date.fromisoformat(match.group(2))
    except ValueError:
        return None

    strike = float(match.group(3))
    opt_type = OptionType.CALL if match.group(4).upper() == "C" else OptionType.PUT
    return exp_date, strike, opt_type


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return f if f == f else None
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
