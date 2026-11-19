from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, ForeignKey, Numeric, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

sale_content = Table(
    "sale_content",
    Base.metadata,
    Column(
        "sale_id",
        ForeignKey("sales.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "product_id",
        ForeignKey("products.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
)


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("sale_revenue >= 0", name="revenue_non_negative"),
        CheckConstraint("sale_cost >= 0", name="cost_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    sale_date: Mapped[date]
    sale_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))

    user: Mapped["User"] = relationship(back_populates="sales")
    products: Mapped[list["Product"]] = relationship(
        secondary=sale_content, back_populates="sales"
    )

    def __repr__(self) -> str:
        return f"Sale(id={self.id!r}, sale_date={self.sale_date!r})"
