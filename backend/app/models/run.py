from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    suite_id: Mapped[int] = mapped_column(ForeignKey("test_suites.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_variant_id: Mapped[int | None] = mapped_column(ForeignKey("prompt_variants.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, running, completed, failed
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    suite: Mapped["TestSuite"] = relationship("TestSuite", back_populates="runs")
    prompt_variant: Mapped["PromptVariant | None"] = relationship("PromptVariant", back_populates="runs")
    results: Mapped[list["RunResult"]] = relationship("RunResult", back_populates="run", cascade="all, delete-orphan")
    summary: Mapped["RunSummary | None"] = relationship("RunSummary", back_populates="run", uselist=False)


class RunResult(Base):
    __tablename__ = "run_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"), nullable=False)
    response_text: Mapped[str | None] = mapped_column(Text)
    score: Mapped[int | None] = mapped_column(Integer)
    pass_: Mapped[bool | None] = mapped_column("pass", Boolean)
    strengths: Mapped[list | None] = mapped_column(JSON)
    weaknesses: Mapped[list | None] = mapped_column(JSON)
    reasoning: Mapped[str | None] = mapped_column(Text)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped["Run"] = relationship("Run", back_populates="results")
    test_case: Mapped["TestCase"] = relationship("TestCase", back_populates="results")


class RunSummary(Base):
    __tablename__ = "run_summary"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), unique=True, nullable=False)
    avg_score: Mapped[float | None] = mapped_column(Float)
    pass_rate: Mapped[float | None] = mapped_column(Float)
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped["Run"] = relationship("Run", back_populates="summary")
