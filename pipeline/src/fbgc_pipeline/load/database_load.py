"""Replace the database contents in one transaction, so a load can be repeated safely.

It writes the catalogue, the participants, their feature values and the demo traces.
Predictions refer to participants, so they are cleared too (the ML publish step rewrites them).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import URL, Connection, create_engine, delete, insert, make_url

from fbgc_core.catalogue_model import Catalogue
from fbgc_core.db.models import (
    Base,
    CatalogueEntry,
    FeatureValue,
    Participant,
    PipelineTrace,
    Prediction,
)
from fbgc_pipeline.load.sources import LoadBundle, LoadError

LOCAL_BACKENDS = frozenset({"sqlite", "postgresql"})
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
REMOTE_QUERY_KEYS = frozenset({"host", "hostaddr", "service", "servicefile", "passfile"})
CLEARED = (Prediction, FeatureValue, PipelineTrace, Participant, CatalogueEntry)
BATCH = 5000


def is_local_database(database_url: str | URL) -> bool:
    """Fail closed: SQLite, or PostgreSQL on a named local host with no host-redirecting query."""
    url = make_url(database_url)
    if url.get_backend_name() not in LOCAL_BACKENDS:
        return False
    if url.get_backend_name() == "sqlite":
        return True
    if url.host not in LOCAL_HOSTS:
        return False
    return not {key.lower() for key in url.query} & REMOTE_QUERY_KEYS


def catalogue_rows(catalogue: Catalogue) -> list[dict[str, Any]]:
    return [
        {**spec.model_dump(), "display_order": order}
        for order, spec in enumerate(catalogue.features)
    ]


def participant_rows(bundle: LoadBundle) -> list[dict[str, Any]]:
    return [
        {
            "pid": str(row["pid"]),
            "wave": int(row["wave"]),
            "gender": str(row["gender"]),
            "age_band": str(row["age_band"]),
            "relationship": str(row["relationship"]),
            "has_messages": bool(row["has_messages"]),
            "has_survey": bool(row["has_survey"]),
            "split_2019": None,
        }
        for row in bundle.participants.to_dict("records")
    ]


def value_rows(bundle: LoadBundle, keys: set[str]) -> list[dict[str, Any]]:
    long = bundle.features_long
    unknown = sorted(set(long["feature_key"].astype(str)) - keys)
    if unknown:
        raise LoadError(f"feature keys not in the catalogue: {unknown[:5]}")
    if not set(long["pid"].astype(str)) <= set(bundle.participants["pid"].astype(str)):
        raise LoadError("feature values for participants that are not loaded")
    return [
        {"pid": str(pid), "feature_key": str(key), "value": float(value)}
        for pid, key, value in zip(long["pid"], long["feature_key"], long["value"], strict=True)
    ]


def insert_rows(connection: Connection, model: type[Base], rows: Sequence[dict[str, Any]]) -> None:
    for start in range(0, len(rows), BATCH):
        connection.execute(insert(model), list(rows[start : start + BATCH]))


def load_database(url: str | URL, bundle: LoadBundle, catalogue: Catalogue) -> dict[str, int]:
    participants = participant_rows(bundle)
    values = value_rows(bundle, set(catalogue.keys()))
    engine = create_engine(url, hide_parameters=True)
    try:
        with engine.begin() as connection:
            for model in CLEARED:
                connection.execute(delete(model))
            insert_rows(connection, CatalogueEntry, catalogue_rows(catalogue))
            insert_rows(connection, Participant, participants)
            insert_rows(connection, FeatureValue, values)
            insert_rows(connection, PipelineTrace, bundle.traces)
    finally:
        engine.dispose()
    return {
        "catalogue": len(catalogue.features),
        "participants": len(participants),
        "feature_values": len(values),
        "traces": len(bundle.traces),
    }
