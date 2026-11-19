from datetime import date

from sqlalchemy import CheckConstraint, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

report_content = Table(
    "report_content",
    Base.metadata,
    Column(
        "report_id",
        ForeignKey("reports.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "kpi_id",
        ForeignKey("kpis.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("report_finish >= report_start", name="period_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    report_type: Mapped[str] = mapped_column(String(50))
    report_start: Mapped[date]
    report_finish: Mapped[date]
    file_path: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))

    user: Mapped["User"] = relationship(back_populates="reports")
    kpis: Mapped[list["Kpi"]] = relationship(
        secondary=report_content, back_populates="reports"
    )

    def __repr__(self) -> str:
        return f"Report(id={self.id!r}, report_type={self.report_type!r})"
