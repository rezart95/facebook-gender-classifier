"""All pages of one export, parsed. Missing pages give empty lists or None."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fbgc_pipeline.parse.events_page import parse_events_page
from fbgc_pipeline.parse.friends_page import parse_friends_page
from fbgc_pipeline.parse.messages_page import parse_messages_page
from fbgc_pipeline.parse.records import EventStats, FriendStats, Thread, WallItem
from fbgc_pipeline.parse.wall_page import parse_wall_page


@dataclass(frozen=True)
class ExportPages:
    threads: list[Thread]
    wall: list[WallItem]
    friends: FriendStats | None
    events: EventStats | None

    @classmethod
    def read(cls, root: Path) -> ExportPages:
        html_dir = root / "html"
        messages = html_dir / "messages.htm"
        wall = html_dir / "wall.htm"
        if not wall.is_file():
            wall = html_dir / "timeline.htm"
        friends = html_dir / "friends.htm"
        events = html_dir / "events.htm"
        return cls(
            threads=parse_messages_page(messages) if messages.is_file() else [],
            wall=parse_wall_page(wall) if wall.is_file() else [],
            friends=parse_friends_page(friends) if friends.is_file() else None,
            events=parse_events_page(events) if events.is_file() else None,
        )
