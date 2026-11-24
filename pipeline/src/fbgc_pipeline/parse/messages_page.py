"""Read chats (html/messages.htm) into threads of messages.

Each div.thread starts with a text node listing the participants, followed by
alternating div.message headers (sender, timestamp) and <p> bodies.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from fbgc_pipeline.parse.html_loading import clean_text, find_all, full_text, load_tree
from fbgc_pipeline.parse.records import Message, Thread
from fbgc_pipeline.parse.timestamps import try_parse_fb_timestamp

Header = tuple[str, str]


def parse_messages_page(path: Path) -> list[Thread]:
    tree = load_tree(path, keep_nesting=False)
    return [_parse_thread(node) for node in find_all(tree, "//div[@class='thread']")]


def _parse_thread(node: etree._Element) -> Thread:
    participants = tuple(name.strip() for name in (node.text or "").split(",") if name.strip())
    messages: list[Message] = []
    header: Header | None = None
    for child in node:
        if child.tag == "div" and child.get("class") == "message":
            if header is not None:
                messages.append(_message(header, ""))
            header = _header(child)
        elif child.tag == "p" and header is not None:
            messages.append(_message(header, full_text(child)))
            header = None
    if header is not None:
        messages.append(_message(header, ""))
    return Thread(participants=participants, messages=tuple(messages))


def _header(node: etree._Element) -> Header:
    users = find_all(node, ".//span[@class='user']")
    metas = find_all(node, ".//span[@class='meta']")
    return (clean_text(users[0]) if users else "", clean_text(metas[0]) if metas else "")


def _message(header: Header, text: str) -> Message:
    sender, meta = header
    return Message(sender=sender, sent_at=try_parse_fb_timestamp(meta), text=text)
