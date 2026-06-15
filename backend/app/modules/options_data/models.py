import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Ticker(Base):
    __tablename__ = "tickers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # equity, index, etf
    exchange: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    contracts: Mapped[list["OptionsContract"]] = relationship(back_populates="ticker")


class OptionsContract(Base):
    __tablename__ = "options_contracts"
    __table_args__ = (
        Index("idx_contracts_ticker_exp", "ticker_id", "expiration_date"),
        Index("idx_contracts_strike_type", "ticker_id", "strike", "option_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickers.id"), nullable=False
    )
    occ_symbol: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    expiration_date: Mapped[date] = mapped_column(nullable=False)
    strike: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    option_type: Mapped[str] = mapped_column(String(4), nullable=False)  # call, put
    multiplier: Mapped[int] = mapped_column(Integer, default=100)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ticker: Mapped["Ticker"] = relationship(back_populates="contracts")
    snapshots: Mapped[list["OptionsSnapshot"]] = relationship(back_populates="contract")


class UnderlyingBar(Base):
    __tablename__ = "underlying_bars"
    __table_args__ = (
        Index("idx_underlying_bars_lookup", "ticker_id", "interval", "timestamp"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickers.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interval: Mapped[str] = mapped_column(String(5), nullable=False)
    open: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OptionsBar(Base):
    __tablename__ = "options_bars"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("options_contracts.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interval: Mapped[str] = mapped_column(String(5), nullable=False)
    open: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    open_interest: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OptionsSnapshot(Base):
    __tablename__ = "options_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("options_contracts.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bid: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    ask: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    last: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    open_interest: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    implied_volatility: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    delta: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    gamma: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    theta: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    vega: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    rho: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    contract: Mapped["OptionsContract"] = relationship(back_populates="snapshots")


class VolatilitySurface(Base):
    __tablename__ = "volatility_surface"
    __table_args__ = (
        Index("idx_vol_surface_lookup", "ticker_id", "surface_date", "expiration_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickers.id"), nullable=False
    )
    surface_date: Mapped[date] = mapped_column(nullable=False)
    expiration_date: Mapped[date] = mapped_column(nullable=False)
    strike: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    iv: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class HistoricalVolatility(Base):
    __tablename__ = "historical_volatility"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickers.id"), nullable=False
    )
    calc_date: Mapped[date] = mapped_column(nullable=False)
    hv_20: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    hv_30: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    hv_60: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    hv_90: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
