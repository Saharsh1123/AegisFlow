from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import CheckConstraint, DateTime, Numeric
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    __table_args__ = (
        CheckConstraint(
            "status IN ('accepted', 'rejected')",
            name="ck_events_status_valid",
        ),
        CheckConstraint(
            "side IN ('BUY', 'SELL')",
            name="ck_events_side_valid",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_events_quantity_positive",
        ),
        CheckConstraint(
            "order_value > 0",
            name="ck_events_order_value_positive",
        ),
        CheckConstraint(
            "price > 0",
            name="ck_events_price_positive",
        ),
        CheckConstraint(
            "event_type IN ('ORDER_SUBMITTED', 'ORDER_CANCELLED', 'ORDER_FILLED', 'RISK_CHECK_REQUESTED')",
            name="ck_events_event_type_valid"
        ),
        CheckConstraint(
            "char_length(asset) BETWEEN 1 AND 30",
            name="ck_events_asset_length_valid",
        )
    )

    event_id: Mapped[UUID] = mapped_column(primary_key=True, nullable=False)

    status: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    risk_approved: Mapped[bool] = mapped_column(nullable=False)

    risk_reason: Mapped[str | None] = mapped_column(nullable=True)

    order_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)

    event_type: Mapped[str] = mapped_column(nullable=False)

    asset: Mapped[str] = mapped_column(nullable=False)

    side: Mapped[str] = mapped_column(nullable=False)

    quantity: Mapped[int] = mapped_column(nullable=False)

    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)

