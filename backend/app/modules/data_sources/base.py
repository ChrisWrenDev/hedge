from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class AssetType(str, Enum):
    EQUITY = "equity"
    INDEX = "index"
    ETF = "etf"


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


@dataclass
class NormalizedContract:
    occ_symbol: str
    underlying_symbol: str
    expiration_date: date
    strike: float
    option_type: OptionType
    multiplier: int = 100
    active: bool = True


@dataclass
class NormalizedSnapshot:
    occ_symbol: str
    underlying_symbol: str
    timestamp: datetime
    bid: float | None = None
    ask: float | None = None
    last: float | None = None
    volume: int | None = None
    open_interest: int | None = None
    implied_volatility: float | None = None
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    rho: float | None = None


@dataclass
class NormalizedUnderlyingBar:
    symbol: str
    timestamp: datetime
    interval: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class FetchResult:
    contracts: list[NormalizedContract] = field(default_factory=list)
    snapshots: list[NormalizedSnapshot] = field(default_factory=list)
    underlying_bars: list[NormalizedUnderlyingBar] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class BaseDataAdapter(ABC):
    name: str

    @abstractmethod
    async def fetch_options_chain(self, symbol: str) -> list[NormalizedContract]:
        """Fetch available option contracts for a symbol."""
        ...

    @abstractmethod
    async def fetch_snapshots(self, symbol: str) -> list[NormalizedSnapshot]:
        """Fetch current snapshots (bid/ask/IV/Greeks) for all options on a symbol."""
        ...

    @abstractmethod
    async def fetch_underlying_bar(self, symbol: str, interval: str = "1d") -> NormalizedUnderlyingBar | None:
        """Fetch latest OHLCV bar for the underlying."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the data source is reachable."""
        ...
