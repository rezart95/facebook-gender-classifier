"""Count friends and friend requests (html/friends.htm) by section label.

myFBr counted the first four lists by position, but real exports insert extra
sections such as "Friend Peer Group", so sections are matched by their heading.
"""

from __future__ import annotations

from pathlib import Path

from fbgc_pipeline.parse.html_loading import clean_text, find_all, load_tree
from fbgc_pipeline.parse.records import FriendStats

SECTION_FIELDS = {
    "amici": "accepted",
    "friends": "accepted",
    "richieste di amicizia inviate": "requests_sent",
    "sent friend requests": "requests_sent",
    "richieste di amicizia ricevute": "requests_received",
    "received friend requests": "requests_received",
    "amici rimossi": "removed",
    "removed friends": "removed",
}


def parse_friends_page(path: Path) -> FriendStats:
    tree = load_tree(path, keep_nesting=False)
    counts: dict[str, int] = dict.fromkeys(
        ("accepted", "requests_sent", "requests_received", "removed"), 0
    )
    for heading in find_all(tree, "//div[@class='contents']//h2"):
        field = SECTION_FIELDS.get(clean_text(heading).lower())
        following = heading.getnext()
        if field is not None and following is not None and following.tag == "ul":
            counts[field] = len(find_all(following, "./li"))
    return FriendStats(**counts)
