"""All faithful (2019) features of one export."""

from __future__ import annotations

from fbgc_pipeline.features.faithful.dictionary import dictionary_counts, load_dictionary
from fbgc_pipeline.features.faithful.gini import gini_heterogeneity
from fbgc_pipeline.features.faithful.message_stats import message_summary
from fbgc_pipeline.features.faithful.name_gender import contact_gender_shares, load_name_vocabulary
from fbgc_pipeline.features.faithful.rhythms import (
    WeekdayLabels,
    days_active,
    hour_shares,
    weekday_shares,
)
from fbgc_pipeline.features.faithful.wall_features import friends_events_features, wall_features
from fbgc_pipeline.parse.export_pages import ExportPages
from fbgc_pipeline.parse.records import Thread
from fbgc_pipeline.window.observation import Bounds, filter_threads, filter_wall
from fbgc_pipeline.window.owner import find_owner


def windowed_threads_and_owner(
    threads: list[Thread], bounds: Bounds
) -> tuple[list[Thread], str | None]:
    """Keep messages inside the window, then find the owner among what remains (as myFBr did)."""
    kept = filter_threads(threads, bounds)
    return kept, find_owner(kept)


def faithful_features(
    pages: ExportPages, bounds: Bounds, weekday_labels: WeekdayLabels
) -> dict[str, float]:
    threads, owner = windowed_threads_and_owner(pages.threads, bounds)
    messages = [message for thread in threads for message in thread.messages]
    senders = [message.sender for message in messages]
    times = [message.sent_at for message in messages]
    features = message_summary(messages)
    features["msg_contact_gini"] = gini_heterogeneity(senders)
    features |= contact_gender_shares(senders, load_name_vocabulary())
    features |= hour_shares(times, "msg")
    features |= weekday_shares(times, "msg", weekday_labels)
    features["msg_days_active"] = days_active(times)
    features |= dictionary_counts(threads, owner, load_dictionary())
    features |= wall_features(filter_wall(pages.wall, bounds), weekday_labels)
    features |= friends_events_features(pages.friends, pages.events)
    return features
