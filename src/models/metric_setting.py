
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class MetricSetting(Base):
    __tablename__ = "metric_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(100), unique=True)
    metric_formula: Mapped[str] = mapped_column(String(400))
    metric_use: Mapped[bool] = mapped_column(default=True)

    kpis: Mapped[list["Kpi"]] = relationship(back_populates="metric")

    def __repr__(self) -> str:
        return f"MetricSetting(id={self.id!r}, metric_name={self.metric_name!r})"
