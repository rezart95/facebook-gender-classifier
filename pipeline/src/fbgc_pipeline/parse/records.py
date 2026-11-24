"""Typed records parsed from an export. They live in memory only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from fbgc_pipeline.locate.language import Language

Gender = Literal["M", "F"]


@dataclass(frozen=True)
class ProfileInfo:
    language: Language
    gender: Gender | None
    gender_raw: str | None
    birth_date: date | None
    registered_at: datetime | None
    downloaded_at: datetime | None
    relationship: str | None


@dataclass(frozen=True)
class Message:
    sender: str
    sent_at: datetime | None
    text: str


@dataclass(frozen=True)
class Thread:
    participants: tuple[str, ...]
    messages: tuple[Message, ...]

    @property
    def is_group(self) -> bool:
        return len(self.participants) > 2


@dataclass(frozen=True)
class WallItem:
    at: datetime | None
    action: str | None
    text: str | None


@dataclass(frozen=True)
class FriendStats:
    accepted: int
    requests_sent: int
    requests_received: int
    removed: int


@dataclass(frozen=True)
class EventStats:
    going: int
    maybe: int
    declined: int
    no_reply: int
