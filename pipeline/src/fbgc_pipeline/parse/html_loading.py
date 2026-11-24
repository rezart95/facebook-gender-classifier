"""Load export pages with lxml, plus small helpers for typed XPath results.

Strict XML keeps the export's own nesting (wall items put <div> inside <p>,
which an HTML parser would break apart). When a page is not well-formed XML,
pages that depend on that nesting get a recovering XML parse; all other pages
get lxml's HTML parser, which also understands HTML entities and bare '&'.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import cast

from lxml import etree, html


def load_tree(path: Path, keep_nesting: bool) -> etree._Element:
    data = path.read_bytes()
    try:
        return etree.fromstring(data, etree.XMLParser(huge_tree=True))
    except etree.XMLSyntaxError:
        if keep_nesting:
            recovered = etree.fromstring(data, etree.XMLParser(recover=True, huge_tree=True))
            if recovered is not None:
                return recovered
        return html.fromstring(data)


def find_all(node: etree._Element, path: str, **variables: str) -> list[etree._Element]:
    xpath = cast("Callable[..., object]", node.xpath)  # lxml-stubs reject XPath variables
    result = xpath(path, **variables)
    if not isinstance(result, list):
        return []
    return [item for item in result if isinstance(item, etree._Element)]


def find_texts(node: etree._Element, path: str) -> list[str]:
    result = node.xpath(path)
    return [str(item) for item in result] if isinstance(result, list) else []


def full_text(node: etree._Element) -> str:
    return "".join(cast("Iterable[str]", node.itertext()))


def clean_text(node: etree._Element | None) -> str:
    """Whitespace-normalised text of a node, or '' when there is no node."""
    return " ".join(full_text(node).split()) if node is not None else ""
