"""Expand templated catalogue families into one entry per feature."""

from __future__ import annotations

import itertools
from typing import Any


def expand_family(family: dict[str, Any]) -> list[dict[str, Any]]:
    name, origin = family["name"], family["origin"]
    if "features" in family:
        return [_entry(name, origin, raw) for raw in family["features"]]
    template: dict[str, str] = family["template"]
    expand: dict[str, list[Any]] = family["expand"]
    missing = set(family.get("legacy_missing", []))
    variables = list(expand)
    entries = []
    for combination in itertools.product(*(expand[variable] for variable in variables)):
        values = dict(zip(variables, combination, strict=True))
        raw: dict[str, Any] = {
            field: str(text).format(**values) for field, text in template.items()
        }
        if raw.get("legacy") in missing:
            raw["legacy"] = None
        entries.append(_entry(name, origin, raw))
    return entries


def _entry(family: str, origin: str, raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": str(raw["key"]).lower(),
        "family": family,
        "origin": str(origin),
        "unit": raw["unit"],
        "description_en": raw["en"],
        "description_it": raw["it"],
        "legacy_name": raw.get("legacy"),
    }
