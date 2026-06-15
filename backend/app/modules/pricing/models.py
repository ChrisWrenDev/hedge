import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.options_data.models import Base


class GreeksSnapshot(Base):
    __tablename__ = "greeks_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("options_contracts.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # "calculated" or "provider"
    spot_price: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    time_to_expiry: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    delta: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    gamma: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    theta: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    vega: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    rho: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    theoretical_price: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
