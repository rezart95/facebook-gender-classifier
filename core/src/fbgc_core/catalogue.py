"""Load the feature catalogue, the single source of truth for every feature."""

from __future__ import annotations

from functools import cache
from pathlib import Path

import yaml

from fbgc_core.catalogue_expand import expand_family
from fbgc_core.catalogue_model import Catalogue, FeatureSpec

DEFAULT_PATH = Path(__file__).resolve().parents[3] / "catalogue" / "features.yaml"


def load_catalogue(path: Path = DEFAULT_PATH) -> Catalogue:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    entries = [entry for family in data["families"] for entry in expand_family(family)]
    features = tuple(FeatureSpec(**entry) for entry in entries)
    return Catalogue(version=data["version"], features=features)


@cache
def default_catalogue() -> Catalogue:
    return load_catalogue()
