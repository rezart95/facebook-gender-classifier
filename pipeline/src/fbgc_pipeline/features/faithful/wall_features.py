"""Faithful wall, friends and events features (myFBr's getWall_summary, getFriends, getEvents).

Wall actions are R grep patterns on the Italian action text, so English exports score
zero here, exactly as in 2019. The `fixed` feature family adds English in milestone 1b.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

from fbgc_pipeline.features.faithful.rhythms import (
    WeekdayLabels,
    days_active,
    hour_shares,
    weekday_shares,
)
from fbgc_pipeline.parse.records import EventStats, FriendStats, WallItem

WALL_ACTION_PATTERNS = {
    key: re.compile(pattern)
    for key, pattern in {
        "wall_friendships": "hanno stretto amicizia",
        "wall_status_updates": "ha aggiornato il suo stato",
        "wall_likes": " piace ",
        "wall_shared_photos": "ha condiviso la foto",
        "wall_links_by_others": "ha pubblicato un link sul tuo diario.",
        "wall_links_by_owner": "ha condiviso un link.",
        "wall_attended": "ha partecipato a",
        "wall_posts_by_others": "scritto sul tuo diario",
        "wall_profile_picture_updates": "aggiornato la sua immagine del profilo",
        "wall_new_photos": "aggiunto una nuova foto all'album",
    }.items()
}


def wall_features(items: Sequence[WallItem], weekday_labels: WeekdayLabels) -> dict[str, float]:
    features = {
        key: float(
            sum(1 for item in items if item.action is not None and pattern.search(item.action))
        )
        for key, pattern in WALL_ACTION_PATTERNS.items()
    }
    features["wall_items_total"] = float(len(items))
    times = [item.at for item in items]
    features |= hour_shares(times, "wall")
    features |= weekday_shares(times, "wall", weekday_labels)
    features["wall_days_active"] = days_active(times)
    return features


def friends_events_features(
    friends: FriendStats | None, events: EventStats | None
) -> dict[str, float]:
    nan = math.nan
    return {
        "friends_accepted": float(friends.accepted) if friends else nan,
        "friends_requests_sent": float(friends.requests_sent) if friends else nan,
        "friends_requests_received": float(friends.requests_received) if friends else nan,
        "friends_removed": float(friends.removed) if friends else nan,
        "events_going": float(events.going) if events else nan,
        "events_maybe": float(events.maybe) if events else nan,
        "events_declined": float(events.declined) if events else nan,
        "events_no_reply": float(events.no_reply) if events else nan,
    }
