import logging
from datetime import date, datetime, timezone

from app.modules.data_sources.base import (
    BaseDataAdapter,
    NormalizedContract,
    NormalizedSnapshot,
    NormalizedUnderlyingBar,
    OptionType,
)

logger = logging.getLogger(__name__)


class YahooAdapter(BaseDataAdapter):
    name = "yahoo"

    def fetch_options_chain(self, symbol: str) -> list[NormalizedContract]:
        contracts = []
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)

            for exp_date_str in ticker.options:
                try:
                    exp_date = date.fromisoformat(exp_date_str)
                except ValueError:
                    continue

                chain = ticker.option_chain(exp_date_str)
                for _, row in chain.calls.iterrows():
                    occ = f"{symbol} {exp_date_str} {row.get('strike', 0)} C"
                    contracts.append(NormalizedContract(
                        occ_symbol=occ,
                        underlying_symbol=symbol.upper(),
                        expiration_date=exp_date,
                        strike=float(row.get("strike", 0)),
                        option_type=OptionType.CALL,
                    ))

                for _, row in chain.puts.iterrows():
                    occ = f"{symbol} {exp_date_str} {row.get('strike', 0)} P"
                    contracts.append(NormalizedContract(
                        occ_symbol=occ,
                        underlying_symbol=symbol.upper(),
                        expiration_date=exp_date,
                        strike=float(row.get("strike", 0)),
                        option_type=OptionType.PUT,
                    ))

        except ImportError:
            logger.error("yfinance not installed: pip install yfinance")
        except Exception as e:
            logger.error(f"Yahoo fetch_options_chain failed: {e}")

        return contracts

    def fetch_snapshots(self, symbol: str) -> list[NormalizedSnapshot]:  # type: ignore[override]
        snapshots = []
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)

            for exp_date_str in ticker.options:
                try:
                    exp_date = date.fromisoformat(exp_date_str)
                except ValueError:
                    continue

                chain = ticker.option_chain(exp_date_str)
                now = datetime.now(timezone.utc)

                for _, row in chain.calls.iterrows():
                    occ = f"{symbol} {exp_date_str} {row.get('strike', 0)} C"
                    snapshots.append(NormalizedSnapshot(
                        occ_symbol=occ,
                        underlying_symbol=symbol.upper(),
                        timestamp=now,
                        bid=_safe_float(row.get("bid")),
                        ask=_safe_float(row.get("ask")),
                        last=_safe_float(row.get("lastPrice")),
                        volume=_safe_int(row.get("volume")),
                        open_interest=_safe_int(row.get("openInterest")),
                        implied_volatility=_safe_float(row.get("impliedVolatility")),
                    ))

                for _, row in chain.puts.iterrows():
                    occ = f"{symbol} {exp_date_str} {row.get('strike', 0)} P"
                    snapshots.append(NormalizedSnapshot(
                        occ_symbol=occ,
                        underlying_symbol=symbol.upper(),
                        timestamp=now,
                        bid=_safe_float(row.get("bid")),
                        ask=_safe_float(row.get("ask")),
                        last=_safe_float(row.get("lastPrice")),
                        volume=_safe_int(row.get("volume")),
                        open_interest=_safe_int(row.get("openInterest")),
                        implied_volatility=_safe_float(row.get("impliedVolatility")),
                    ))

        except ImportError:
            logger.error("yfinance not installed")
        except Exception as e:
            logger.error(f"Yahoo fetch_snapshots failed: {e}")

        return snapshots

    def fetch_underlying_bar(self, symbol: str, interval: str = "1d") -> NormalizedUnderlyingBar | None:  # type: ignore[override]
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval=interval)

            if hist.empty:
                return None

            last = hist.iloc[-1]
            return NormalizedUnderlyingBar(
                symbol=symbol.upper(),
                timestamp=datetime.now(timezone.utc),
                interval=interval,
                open=float(last.get("Open", 0)),
                high=float(last.get("High", 0)),
                low=float(last.get("Low", 0)),
                close=float(last.get("Close", 0)),
                volume=int(last.get("Volume", 0)),
            )

        except ImportError:
            logger.error("yfinance not installed")
        except Exception as e:
            logger.error(f"Yahoo fetch_underlying_bar failed: {e}")

        return None

    async def health_check(self) -> bool:
        try:
            import yfinance as yf
            ticker = yf.Ticker("SPY")
            _ = ticker.info
            return True
        except Exception:
            return False


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return f if f == f else None  # NaN check
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
