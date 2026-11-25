"""Tests never see the owner's real settings: the variables below are removed for every test.

A test that needs one of them sets it itself with `monkeypatch.setenv`.
"""

import pytest

OWNER_ENVIRONMENT = (
    "FBGC_RAW_DIR",
    "FBGC_PRIVATE_DIR",
    "FBGC_ID_SECRET",
    "DATABASE_URL",
    "PGHOSTADDR",
    "PGSERVICE",
)


@pytest.fixture(autouse=True)
def isolate_owner_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in OWNER_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)
