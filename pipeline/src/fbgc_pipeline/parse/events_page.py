"""Count event responses (html/events.htm) the way myFBr did: Italian labels only."""

from __future__ import annotations

from pathlib import Path

from fbgc_pipeline.parse.html_loading import find_all, full_text, load_tree
from fbgc_pipeline.parse.records import EventStats

RESPONSES = {
    "going": "Partecipazione confermata",
    "maybe": "Forse",
    "declined": "Partecipazione rifiutata",
    "no_reply": "Nessuna risposta",
}


def parse_events_page(path: Path) -> EventStats:
    tree = load_tree(path, keep_nesting=False)
    tails = [full_text(paragraph).split(" - ")[-1] for paragraph in find_all(tree, "//ul/li/p")]
    counts = {field: sum(label in tail for tail in tails) for field, label in RESPONSES.items()}
    return EventStats(**counts)
