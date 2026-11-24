"""Read wall items (html/wall.htm, or timeline.htm in some exports).

myFBr took the children of each <p> in order: [time, action, text]. When an
item has no action text, the comment slides into the action slot; that quirk
is kept so the 2019 features can be reproduced.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from fbgc_pipeline.parse.html_loading import find_all, full_text, load_tree
from fbgc_pipeline.parse.records import WallItem
from fbgc_pipeline.parse.timestamps import try_parse_fb_timestamp


def parse_wall_page(path: Path) -> list[WallItem]:
    tree = load_tree(path, keep_nesting=True)
    items = []
    for paragraph in find_all(tree, "//div[@class='contents']/div/p"):
        values = child_values(paragraph)
        if not values:
            continue
        items.append(
            WallItem(
                at=try_parse_fb_timestamp(" ".join(values[0].split())),
                action=values[1] if len(values) > 1 else None,
                text=values[2] if len(values) > 2 else None,
            )
        )
    return items


def child_values(paragraph: etree._Element) -> list[str]:
    """Element texts and non-blank text nodes, in document order (R's xmlChildren)."""
    values = [paragraph.text] if paragraph.text and paragraph.text.strip() else []
    for child in paragraph:
        values.append(full_text(child))
        if child.tail and child.tail.strip():
            values.append(child.tail)
    return values
