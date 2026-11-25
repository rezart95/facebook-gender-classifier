"""Initial schema: participants, catalogue, feature values, model results, traces.

Revision ID: 0001
Revises:
Create Date: 2026-11-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None

TABLES = (
    "pipeline_traces",
    "stepwise_trace",
    "predictions",
    "model_coefficients",
    "model_metrics",
    "model_runs",
    "feature_values",
    "feature_catalogue",
    "participants",
)


def required(name: str, kind: sa.types.TypeEngine) -> sa.Column:
    return sa.Column(name, kind, nullable=False)


def surrogate_id() -> sa.Column:
    return sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True)


def run_fk() -> sa.Column:
    return sa.Column("run_id", sa.String(64), sa.ForeignKey("model_runs.run_id"), nullable=False)


def upgrade() -> None:
    op.create_table(
        "participants",
        sa.Column("pid", sa.String(16), primary_key=True),
        required("wave", sa.Integer()),
        required("gender", sa.String(1)),
        required("age_band", sa.String(16)),
        required("relationship", sa.String(32)),
        required("has_messages", sa.Boolean()),
        required("has_survey", sa.Boolean()),
        sa.Column("split_2019", sa.String(16)),
    )
    op.create_table(
        "feature_catalogue",
        sa.Column("key", sa.String(64), primary_key=True),
        required("family", sa.String(64)),
        required("origin", sa.String(16)),
        required("unit", sa.String(32)),
        required("dtype", sa.String(16)),
        required("description_en", sa.Text()),
        required("description_it", sa.Text()),
        sa.Column("legacy_name", sa.String(128)),
        required("display_order", sa.Integer()),
    )
    op.create_table(
        "feature_values",
        sa.Column("pid", sa.String(16), sa.ForeignKey("participants.pid"), primary_key=True),
        sa.Column(
            "feature_key", sa.String(64), sa.ForeignKey("feature_catalogue.key"), primary_key=True
        ),
        required("value", sa.Float()),
    )
    op.create_table(
        "model_runs",
        sa.Column("run_id", sa.String(64), primary_key=True),
        required("era", sa.String(16)),
        required("model_type", sa.String(64)),
        required("params", sa.JSON()),
        sa.Column("cv_scheme", sa.String(128)),
        required("created_at", sa.DateTime(timezone=True)),
        sa.Column("mlflow_run_id", sa.String(64)),
    )
    op.create_table(
        "model_metrics",
        surrogate_id(),
        run_fk(),
        required("metric", sa.String(64)),
        sa.Column("fold", sa.Integer()),
        required("value", sa.Float()),
    )
    op.create_table(
        "model_coefficients",
        surrogate_id(),
        run_fk(),
        required("feature_key", sa.String(64)),
        required("estimate", sa.Float()),
        sa.Column("std_error", sa.Float()),
        sa.Column("stat", sa.Float()),
        sa.Column("p_value", sa.Float()),
    )
    op.create_table(
        "predictions",
        surrogate_id(),
        run_fk(),
        sa.Column("pid", sa.String(16), sa.ForeignKey("participants.pid"), nullable=False),
        sa.Column("fold", sa.Integer()),
        required("probability", sa.Float()),
    )
    op.create_table(
        "stepwise_trace",
        sa.Column("run_id", sa.String(64), sa.ForeignKey("model_runs.run_id"), primary_key=True),
        sa.Column("step", sa.Integer(), primary_key=True),
        required("action", sa.String(16)),
        sa.Column("feature_key", sa.String(64)),
        required("aic", sa.Float()),
    )
    op.create_table(
        "pipeline_traces",
        sa.Column("trace_id", sa.String(64), primary_key=True),
        required("profile_label", sa.String(64)),
        required("stages", sa.JSON()),
    )


def downgrade() -> None:
    for table in TABLES:
        op.drop_table(table)
