"""Database schema (spec section 6.8). Generic SQLAlchemy types only, so tests run on SQLite.

Rows are pseudonymous (P-IDs or synthetic S-IDs). Loading happens only through `fbgc load`
and, later, the ML publish step; the API reads with a read-only role.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Participant(Base):
    __tablename__ = "participants"
    pid: Mapped[str] = mapped_column(String(16), primary_key=True)
    wave: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(1))
    age_band: Mapped[str] = mapped_column(String(16))
    relationship: Mapped[str] = mapped_column(String(32))
    has_messages: Mapped[bool] = mapped_column(Boolean)
    has_survey: Mapped[bool] = mapped_column(Boolean)
    split_2019: Mapped[str | None] = mapped_column(String(16))


class CatalogueEntry(Base):
    __tablename__ = "feature_catalogue"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    family: Mapped[str] = mapped_column(String(64))
    origin: Mapped[str] = mapped_column(String(16))
    unit: Mapped[str] = mapped_column(String(32))
    dtype: Mapped[str] = mapped_column(String(16))
    description_en: Mapped[str] = mapped_column(Text)
    description_it: Mapped[str] = mapped_column(Text)
    legacy_name: Mapped[str | None] = mapped_column(String(128))
    display_order: Mapped[int] = mapped_column(Integer)


class FeatureValue(Base):
    __tablename__ = "feature_values"
    pid: Mapped[str] = mapped_column(ForeignKey("participants.pid"), primary_key=True)
    feature_key: Mapped[str] = mapped_column(ForeignKey("feature_catalogue.key"), primary_key=True)
    value: Mapped[float] = mapped_column(Float)


class ModelRun(Base):
    __tablename__ = "model_runs"
    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    era: Mapped[str] = mapped_column(String(16))
    model_type: Mapped[str] = mapped_column(String(64))
    params: Mapped[dict[str, Any]] = mapped_column(JSON)
    cv_scheme: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mlflow_run_id: Mapped[str | None] = mapped_column(String(64))


class ModelMetric(Base):
    __tablename__ = "model_metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("model_runs.run_id"))
    metric: Mapped[str] = mapped_column(String(64))
    fold: Mapped[int | None] = mapped_column(Integer)
    value: Mapped[float] = mapped_column(Float)


class ModelCoefficient(Base):
    __tablename__ = "model_coefficients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("model_runs.run_id"))
    feature_key: Mapped[str] = mapped_column(String(64))
    estimate: Mapped[float] = mapped_column(Float)
    std_error: Mapped[float | None] = mapped_column(Float)
    stat: Mapped[float | None] = mapped_column(Float)
    p_value: Mapped[float | None] = mapped_column(Float)


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("model_runs.run_id"))
    pid: Mapped[str] = mapped_column(ForeignKey("participants.pid"))
    fold: Mapped[int | None] = mapped_column(Integer)
    probability: Mapped[float] = mapped_column(Float)


class StepwiseStep(Base):
    __tablename__ = "stepwise_trace"
    run_id: Mapped[str] = mapped_column(ForeignKey("model_runs.run_id"), primary_key=True)
    step: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(16))
    feature_key: Mapped[str | None] = mapped_column(String(64))
    aic: Mapped[float] = mapped_column(Float)


class PipelineTrace(Base):
    __tablename__ = "pipeline_traces"
    trace_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    profile_label: Mapped[str] = mapped_column(String(64))
    stages: Mapped[list[Any]] = mapped_column(JSON)
