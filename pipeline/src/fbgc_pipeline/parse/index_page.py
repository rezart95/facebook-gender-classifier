"""Read the profile page (index.htm): gender label, dates and relationship status.

Names, e-mail addresses and hometowns are never read.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from lxml import etree

from fbgc_pipeline.locate.language import detect_language
from fbgc_pipeline.parse.html_loading import clean_text, find_all, load_tree
from fbgc_pipeline.parse.records import Gender, ProfileInfo
from fbgc_pipeline.parse.timestamps import find_trailing_timestamp, try_parse_fb_timestamp

GENDER_LABELS = ("Sesso", "Genere", "Gender", "Sex")
GENDER_VALUES: dict[str, Gender] = {
    "uomo": "M",
    "maschio": "M",
    "male": "M",
    "donna": "F",
    "femmina": "F",
    "female": "F",
}
REGISTRATION_LABELS = ("Data di registrazione", "Registration Date")
BIRTH_LABELS = ("Data di nascita", "Birthday")
RELATIONSHIP_LABELS = ("Situazione sentimentale", "Relationship Status")
BIRTH_FORMATS = ("%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%d %B %Y")


def parse_index_page(path: Path) -> ProfileInfo:
    tree = load_tree(path, keep_nesting=False)
    gender_raw = row_value(tree, GENDER_LABELS)
    footers = find_all(tree, "//div[@class='footer']")
    footer_text = clean_text(footers[0]) if footers else ""
    return ProfileInfo(
        language=detect_language(tree),
        gender=GENDER_VALUES.get((gender_raw or "").lower()),
        gender_raw=gender_raw,
        birth_date=parse_birth_date(row_value(tree, BIRTH_LABELS)),
        registered_at=try_parse_fb_timestamp(row_value(tree, REGISTRATION_LABELS)),
        downloaded_at=find_trailing_timestamp(footer_text) if footer_text else None,
        relationship=row_value(tree, RELATIONSHIP_LABELS),
    )


def row_value(tree: etree._Element, labels: tuple[str, ...]) -> str | None:
    for label in labels:
        cells = find_all(tree, "//tr[th[normalize-space()=$label]]/td", label=label)
        if cells:
            return clean_text(cells[0]) or None
    return None


def parse_birth_date(text: str | None) -> date | None:
    if not text:
        return None
    for date_format in BIRTH_FORMATS:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None
