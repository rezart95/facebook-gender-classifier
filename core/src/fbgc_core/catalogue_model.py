"""Typed model of the feature catalogue (catalogue/features.yaml)."""

from __future__ import annotations

import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

Origin = Literal["2019", "fixed", "new"]
KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class FeatureSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    family: str
    origin: Origin
    unit: str
    dtype: Literal["float"] = "float"
    description_en: str
    description_it: str
    legacy_name: str | None = None

    @field_validator("key")
    @classmethod
    def key_is_snake_case(cls, value: str) -> str:
        if not KEY_PATTERN.match(value):
            raise ValueError(f"feature key must be snake_case: {value!r}")
        return value


class Catalogue(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: int
    features: tuple[FeatureSpec, ...]

    @model_validator(mode="after")
    def names_are_unique(self) -> Catalogue:
        keys = Counter(spec.key for spec in self.features)
        legacy = Counter(spec.legacy_name for spec in self.features if spec.legacy_name)
        for label, counts in (("key", keys), ("legacy name", legacy)):
            duplicates = sorted(name for name, count in counts.items() if count > 1)
            if duplicates:
                raise ValueError(f"duplicate {label}s: {duplicates}")
        return self

    def keys(self, origin: Origin | None = None) -> list[str]:
        return [spec.key for spec in self.features if origin is None or spec.origin == origin]

    def get(self, key: str) -> FeatureSpec:
        for spec in self.features:
            if spec.key == key:
                return spec
        raise KeyError(key)

    def legacy_to_key(self) -> dict[str, str]:
        return {spec.legacy_name: spec.key for spec in self.features if spec.legacy_name}
