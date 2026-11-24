"""Fake profile content for tests and for the animated demo. All names are invented."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fbgc_pipeline.synthetic.timestamp_format import Style

ROME_WINTER = timezone(timedelta(hours=1))
ROME_SUMMER = timezone(timedelta(hours=2))
DEFAULT_FRIEND_SECTIONS = (
    ("Amici", 3),
    ("Friend Peer Group", 2),
    ("Sent Friend Requests", 1),
    ("Richieste di amicizia ricevute", 2),
    ("Amici rimossi", 1),
)


@dataclass(frozen=True)
class FakeMessage:
    sender: str
    sent_at: datetime
    text: str


@dataclass(frozen=True)
class FakeThread:
    participants: tuple[str, ...]
    messages: tuple[FakeMessage, ...]


@dataclass(frozen=True)
class FakeWallItem:
    at: datetime
    action: str | None = None
    comment: str | None = None


@dataclass(frozen=True)
class FakeProfile:
    owner: str
    style: Style = "it"
    gender_label: str = "Donna"
    birthday: str = "03/12/1995"
    registered_at: datetime = datetime(2009, 5, 4, 18, 30, tzinfo=ROME_SUMMER)
    downloaded_at: datetime = datetime(2015, 11, 20, 10, 0, tzinfo=ROME_WINTER)
    relationship: str | None = "Single"
    threads: tuple[FakeThread, ...] = ()
    wall: tuple[FakeWallItem, ...] = ()
    friend_sections: tuple[tuple[str, int], ...] = DEFAULT_FRIEND_SECTIONS
    events: tuple[str, ...] = ()
    break_messages_xml: bool = False
