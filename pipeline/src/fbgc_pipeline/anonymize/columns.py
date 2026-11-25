"""The published shape of the anonymized tables, and the features they may carry.

The scrub check and the table builder both read this module, so the scrub is not limited to
what the builder happens to produce.
"""

from __future__ import annotations

from functools import cache

from fbgc_core.catalogue import default_catalogue

PARTICIPANT_COLUMNS = (
    "pid",
    "wave",
    "gender",
    "age_band",
    "relationship",
    "has_messages",
    "has_survey",
)
FEATURE_COLUMNS = ("pid", "feature_key", "value")
# Columns of the private extraction output that must never be published as features.
PRIVATE_INPUT_COLUMNS = frozenset(
    {
        "wave",
        "folder_code",
        "status",
        "language",
        "gender",
        "age_at_download",
        "relationship",
        "has_survey",
    }
)


@cache
def published_feature_keys() -> frozenset[str]:
    """The faithful 2019 features plus the survey scales: the only keys that may be published."""
    catalogue = default_catalogue()
    return frozenset(catalogue.keys("2019")) | frozenset(catalogue.keys("survey"))
