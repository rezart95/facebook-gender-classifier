"""Inventory of the exports: wave, UI language and which pages exist."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal

from lxml import etree

from fbgc_pipeline.locate.language import Language, detect_language
from fbgc_pipeline.locate.profile_finder import ProfileLocation
from fbgc_pipeline.parse.html_loading import load_tree

RowLanguage = Language | Literal["unreadable"]
EXPECTED_PAGES = ("messages.htm", "wall.htm", "friends.htm", "events.htm")


@dataclass(frozen=True)
class InventoryRow:
    wave: int
    folder_code: str
    language: RowLanguage
    pages: tuple[str, ...]


def inventory_row(location: ProfileLocation) -> InventoryRow:
    pages = tuple(name for name in EXPECTED_PAGES if (location.root / "html" / name).is_file())
    return InventoryRow(location.wave, location.folder_code, _language_of(location), pages)


def _language_of(location: ProfileLocation) -> RowLanguage:
    """The UI language, or "unreadable" when index.htm is missing, empty or unparseable.

    The error itself is dropped on purpose: it could carry a path or page content.
    """
    try:
        return detect_language(load_tree(location.root / "index.htm", keep_nesting=False))
    except (etree.ParserError, etree.XMLSyntaxError, OSError):
        return "unreadable"


def summarise_inventory(
    rows: list[InventoryRow], missing: list[tuple[int, str]]
) -> dict[str, object]:
    """Aggregate counts only, safe to print."""
    return {
        "profiles": len(rows),
        "missing_index": len(missing),
        "by_wave": {str(wave): n for wave, n in sorted(Counter(row.wave for row in rows).items())},
        "by_language": dict(Counter(row.language for row in rows)),
        "pages_present": {page: sum(page in row.pages for row in rows) for page in EXPECTED_PAGES},
    }
