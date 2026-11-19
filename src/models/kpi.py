from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.report import report_content


class Kpi(Base):
    __tablename__ = "kpis"
    __table_args__ = (
        CheckConstraint("kpi_finish >= kpi_start", name="period_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kpi_start: Mapped[date]
    kpi_finish: Mapped[date]
    kpi_value: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    metric_id: Mapped[int] = mapped_column(
        ForeignKey("metric_settings.id", ondelete="RESTRICT")
    )

    metric: Mapped["MetricSetting"] = relationship(back_populates="kpis")
    reports: Mapped[list["Report"]] = relationship(
        secondary=report_content, back_populates="kpis"
    )

    def __repr__(self) -> str:
        return f"Kpi(id={self.id!r}, kpi_value={self.kpi_value!r})"
