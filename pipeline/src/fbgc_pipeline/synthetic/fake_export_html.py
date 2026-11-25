"""Render fake exports in the 2015 Facebook HTML format (one line, no indentation)."""

from __future__ import annotations

from datetime import datetime
from html import escape

from fbgc_pipeline.synthetic.fake_records import FakeProfile, FakeThread, FakeWallItem
from fbgc_pipeline.synthetic.timestamp_format import format_fb_timestamp

LABELS = {
    "it": {
        "profile": "Profilo",
        "email": "E-mail",
        "registered": "Data di registrazione",
        "birthday": "Data di nascita",
        "gender": "Sesso",
        "relationship": "Situazione sentimentale",
        "footer": "Scaricato da {owner} il {when}",
        "events": "Eventi",
    },
    "en": {
        "profile": "Profile",
        "email": "Email",
        "registered": "Registration Date",
        "birthday": "Birthday",
        "gender": "Gender",
        "relationship": "Relationship Status",
        "footer": "Downloaded by {owner} on {when}",
        "events": "Events",
    },
}
FAKE_MARKER = "fake.profile@example.org"  # every fake export carries it; `fbgc trace` checks it
PROFILE_LINK = (
    '<a href="https://www.facebook.com/fake.profile">https://www.facebook.com/fake.profile</a>'
)


def _labels(profile: FakeProfile) -> dict[str, str]:
    return LABELS["it" if profile.style == "it" else "en"]


def _text(value: str) -> str:
    return escape(value, quote=False)


def _when(profile: FakeProfile, moment: datetime) -> str:
    return format_fb_timestamp(moment, profile.style)


def _page(profile: FakeProfile, contents: str) -> str:
    when = _when(profile, profile.downloaded_at)
    footer = _labels(profile)["footer"].format(owner=profile.owner, when=when)
    return (
        '<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />'
        f"<title>{_text(profile.owner)}</title></head><body>"
        f'<div class="contents"><h1>{_text(profile.owner)}</h1>{contents}</div>'
        f'<div class="footer">{_text(footer)}</div></body></html>'
    )


def render_index(profile: FakeProfile) -> str:
    labels = _labels(profile)
    rows = [
        (labels["profile"], PROFILE_LINK),
        (labels["email"], FAKE_MARKER),
        (labels["registered"], _text(_when(profile, profile.registered_at))),
        (labels["birthday"], _text(profile.birthday)),
        (labels["gender"], _text(profile.gender_label)),
    ]
    if profile.relationship:
        rows.append((labels["relationship"], _text(profile.relationship)))
    table = "".join(f"<tr><th>{label}</th><td>{cell}</td></tr>" for label, cell in rows)
    return _page(profile, f"<div><table>{table}</table></div>")


def render_messages(profile: FakeProfile) -> str:
    threads = "".join(_thread(profile, thread) for thread in profile.threads)
    return _page(profile, f"<div>{threads}</div>")


def _thread(profile: FakeProfile, thread: FakeThread) -> str:
    body = "".join(
        '<div class="message"><div class="message_header">'
        f'<span class="user">{_text(message.sender)}</span>'
        f'<span class="meta">{_when(profile, message.sent_at)}</span></div></div>'
        f"<p>{message.text if profile.break_messages_xml else _text(message.text)}</p>"
        for message in thread.messages
    )
    return f'<div class="thread">{_text(", ".join(thread.participants))}{body}</div>'


def render_wall(profile: FakeProfile) -> str:
    items = "".join(_wall_item(profile, item) for item in profile.wall)
    return _page(profile, f"<div>{items}</div>")


def _wall_item(profile: FakeProfile, item: FakeWallItem) -> str:
    action = _text(item.action) if item.action else ""
    comment = f'<div class="comment">{_text(item.comment)}</div>' if item.comment else ""
    return f'<p><div class="meta">{_when(profile, item.at)}</div>{action}{comment}</p>'


def render_friends(profile: FakeProfile) -> str:
    sections = "".join(
        f"<h2>{_text(label)}</h2><ul>"
        + "".join(f"<li>Amico {i}</li>" for i in range(count))
        + "</ul>"
        for label, count in profile.friend_sections
    )
    return _page(profile, f"<div>{sections}</div>")


def render_events(profile: FakeProfile) -> str:
    items = "".join(f"<li><p>{_text(text)}</p></li>" for text in profile.events)
    return _page(profile, f"<div><h2>{_labels(profile)['events']}</h2><ul>{items}</ul></div>")
