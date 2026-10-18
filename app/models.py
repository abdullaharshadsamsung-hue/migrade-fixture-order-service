"""Orders live in Postgres; customer credit limits in the legacy MySQL database."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, LegacyBase


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, index=True)
    product: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer)
    total: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "product": self.product,
            "quantity": self.quantity,
            "total": float(self.total),
            "status": self.status,
        }


class CustomerCredit(LegacyBase):
    __tablename__ = "customer_credit"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    credit_limit: Mapped[float] = mapped_column(Numeric(10, 2))
    used: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
