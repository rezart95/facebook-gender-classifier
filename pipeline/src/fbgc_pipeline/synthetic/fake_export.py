"""Write a fake export to disk in the folder layout of a real one."""

from __future__ import annotations

from pathlib import Path

from fbgc_pipeline.synthetic.fake_export_html import (
    render_events,
    render_friends,
    render_index,
    render_messages,
    render_wall,
)
from fbgc_pipeline.synthetic.fake_records import FakeProfile

PAGES = {
    "messages.htm": render_messages,
    "wall.htm": render_wall,
    "friends.htm": render_friends,
    "events.htm": render_events,
}


def write_fake_export(root: Path, profile: FakeProfile) -> Path:
    """Write index.htm and html/*.htm under `root` and return `root`."""
    (root / "html").mkdir(parents=True, exist_ok=True)
    (root / "index.htm").write_text(render_index(profile), encoding="utf-8", newline="\n")
    for name, render in PAGES.items():
        (root / "html" / name).write_text(render(profile), encoding="utf-8", newline="\n")
    return root
