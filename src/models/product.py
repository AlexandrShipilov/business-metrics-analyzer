from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.sale import sale_content


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[str] = mapped_column(String(100), unique=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"Category(id={self.id!r}, category_name={self.category_name!r})"


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("product_price >= 0", name="price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(100), unique=True)
    product_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT")
    )

    category: Mapped["Category"] = relationship(back_populates="products")
    sales: Mapped[list["Sale"]] = relationship(
        secondary=sale_content, back_populates="products"
    )

    def __repr__(self) -> str:
        return f"Product(id={self.id!r}, product_name={self.product_name!r})"
