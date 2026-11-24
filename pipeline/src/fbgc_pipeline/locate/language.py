"""Detect the UI language of an export from the labels on its profile page."""

from __future__ import annotations

from typing import Literal

from lxml import etree

from fbgc_pipeline.parse.html_loading import find_texts

Language = Literal["it", "en", "other"]
IT_LABELS = frozenset({"Sesso", "Genere", "Data di registrazione", "Data di nascita"})
EN_LABELS = frozenset({"Gender", "Registration Date", "Birthday"})


def detect_language(index_tree: etree._Element) -> Language:
    labels = {" ".join(text.split()) for text in find_texts(index_tree, "//th/text()")}
    if labels & IT_LABELS:
        return "it"
    if labels & EN_LABELS:
        return "en"
    return "other"
