import uuid
from datetime import date, datetime

from sqlalchemy import DateTime, Date, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.options_data.models import Base


class ConvexityScore(Base):
    __tablename__ = "convexity_scores"
    __table_args__ = (
        Index("idx_convexity_rank", "score_date", "score"),
        Index("idx_convexity_contract_date", "contract_id", "score_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("options_contracts.id"), nullable=False
    )
    score_date: Mapped[date] = mapped_column(Date, nullable=False)
    score: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    gamma_per_theta: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)
    vega_normalized: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)
    iv_rank: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    iv_percentile: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    contract: Mapped["OptionsContract"] = relationship()  # noqa: F821
