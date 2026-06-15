import logging
from datetime import date, datetime, timezone

from app.config import settings
from app.modules.data_sources.base import (
    BaseDataAdapter,
    NormalizedContract,
    NormalizedSnapshot,
    NormalizedUnderlyingBar,
    OptionType,
)

logger = logging.getLogger(__name__)


class IBKRAdapter(BaseDataAdapter):
    name = "ibkr"

    def __init__(self) -> None:
        self.host = settings.IBKR_HOST
        self.port = settings.IBKR_PORT
        self.client_id = settings.IBKR_CLIENT_ID
        self._ib = None

    async def _connect(self):
        if self._ib is not None and self._ib.isConnected():
            return self._ib

        try:
            from ib_async import IB
            ib = IB()
            await ib.connect(self.host, self.port, clientId=self.client_id)
            self._ib = ib
            return ib
        except ImportError:
            logger.error("ib_async not installed: pip install ib_async")
            return None
        except Exception as e:
            logger.error(f"IBKR connection failed: {e}")
            return None

    async def fetch_options_chain(self, symbol: str) -> list[NormalizedContract]:
        ib = await self._connect()
        if not ib:
            return []

        contracts = []
        try:
            from ib_async import Stock, Index

            # Try stock first, then index
            underlying = None
            for ContractClass in [Stock, Index]:
                try:
                    chains = await ib.reqSecDefParamsAsync(symbol, "", "", "", "")
                    if chains:
                        for chain in chains:
                            for exp in chain.expirations:
                                for strike in chain.strikes:
                                    for right in ["C", "P"]:
                                        opt_type = OptionType.CALL if right == "C" else OptionType.PUT
                                        occ = f"{symbol} {exp} {strike} {right}"
                                        try:
                                            exp_date = date.fromisoformat(exp)
                                        except ValueError:
                                            continue
                                        contracts.append(NormalizedContract(
                                            occ_symbol=occ,
                                            underlying_symbol=symbol.upper(),
                                            expiration_date=exp_date,
                                            strike=float(strike),
                                            option_type=opt_type,
                                        ))
                    break
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"IBKR fetch_options_chain failed: {e}")

        return contracts

    async def fetch_snapshots(self, symbol: str) -> list[NormalizedSnapshot]:
        ib = await self._connect()
        if not ib:
            return []

        snapshots = []
        try:
            from ib_async import Stock

            contract = Stock(symbol, "SMART", "USD")
            await ib.qualifyContractsAsync(contract)
            tickers = await ib.reqMktDataAsync(contract, snapshot=True)

            for ticker in tickers:
                if ticker.marketPrice() and ticker.marketPrice() == ticker.marketPrice():
                    snapshots.append(NormalizedSnapshot(
                        occ_symbol=symbol,
                        underlying_symbol=symbol.upper(),
                        timestamp=datetime.now(timezone.utc),
                        last=float(ticker.marketPrice()),
                        volume=int(ticker.volume or 0),
                    ))

        except Exception as e:
            logger.error(f"IBKR fetch_snapshots failed: {e}")

        return snapshots

    async def fetch_underlying_bar(self, symbol: str, interval: str = "1d") -> NormalizedUnderlyingBar | None:
        ib = await self._connect()
        if not ib:
            return None

        try:
            from ib_async import Stock, Duration, BarSize

            contract = Stock(symbol, "SMART", "USD")
            await ib.qualifyContractsAsync(contract)

            duration_map = {"1d": Duration.DAYS_1, "1w": Duration.WEEKS_1, "1m": Duration.MONTHS_1}
            barsize_map = {"1m": BarSize.MINS_1, "5m": BarSize.MINS_5, "15m": BarSize.MINS_15, "1h": BarSize.HOURS_1, "1d": BarSize.DAYS_1}

            bars = await ib.reqHistoricalDataAsync(
                contract,
                endDateTime="",
                durationStr=duration_map.get(interval, Duration.DAYS_1),
                barSizeSetting=barsize_map.get(interval, BarSize.DAYS_1),
                whatToShow="TRADES",
                useRTH=True,
            )

            if bars:
                last = bars[-1]
                return NormalizedUnderlyingBar(
                    symbol=symbol.upper(),
                    timestamp=last.date if hasattr(last, 'date') else datetime.now(timezone.utc),
                    interval=interval,
                    open=float(last.open),
                    high=float(last.high),
                    low=float(last.low),
                    close=float(last.close),
                    volume=int(last.volume),
                )

        except Exception as e:
            logger.error(f"IBKR fetch_underlying_bar failed: {e}")

        return None

    async def health_check(self) -> bool:
        ib = await self._connect()
        return ib is not None and ib.isConnected()
