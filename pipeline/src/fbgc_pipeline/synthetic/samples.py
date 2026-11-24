"""An invented sample profile: the test fixture, and later the input of the animated demo."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fbgc_pipeline.synthetic.fake_records import (
    ROME_WINTER,
    FakeMessage,
    FakeProfile,
    FakeThread,
    FakeWallItem,
)

SAMPLE_OWNER = "Giulia Bianchi"


def at(day: int, hour: int, minute: int = 0) -> datetime:
    """A moment in November 2015, Italian winter time (1 November 2015 was a Sunday)."""
    return datetime(2015, 11, day, hour, minute, tzinfo=ROME_WINTER)


def sample_profile(**overrides: Any) -> FakeProfile:
    owner = SAMPLE_OWNER
    personal = FakeThread(
        (owner, "Marco Verdi"),
        (
            FakeMessage(owner, at(2, 9), "Ciao Marco :) come stai?"),
            FakeMessage("Marco Verdi", at(2, 9, 5), "Bene! Tu? non lo so..."),
            FakeMessage(owner, at(8, 23, 30), "ok ahahah"),
        ),
    )
    group = FakeThread(
        (owner, "Marco Verdi", "Sara Neri"),
        (
            FakeMessage("Sara Neri", at(3, 14), "Che palle!!"),
            FakeMessage(owner, at(3, 14, 2), "dai forzaaa \N{GRINNING FACE}"),
        ),
    )
    fields: dict[str, Any] = {
        "owner": owner,
        "threads": (personal, group),
        "wall": (
            FakeWallItem(at(4, 18), f"{owner} ha condiviso un link.", "bello"),
            FakeWallItem(at(5, 20), None, "solo un commento"),
        ),
        "events": (
            "Festa - Sabato 7 novembre 2015 alle ore 21:00 UTC+01 - Partecipazione confermata",
        ),
    }
    fields.update(overrides)
    return FakeProfile(**fields)
