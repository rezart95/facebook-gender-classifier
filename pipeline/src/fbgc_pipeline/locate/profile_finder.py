"""Find each participant's export inside wave1/ and wave2/.

Folders are nested 0–2 levels deep and may contain macOS junk, so the export
root is reached by repeatedly entering the first subfolder (alphabetically)
until one holds index.htm, the same rule myFBr's fixPath used.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

WAVE_DIRS = {"wave1": 1, "wave2": 2}
SKIP_NAMES = frozenset({"__MACOSX", ".DS_Store", ".directory"})
MAX_DEPTH = 10


@dataclass(frozen=True)
class ProfileLocation:
    wave: int
    folder_code: str
    root: Path


def folder_code_from_name(name: str) -> str:
    return re.sub(r"\.zip$", "", name, flags=re.IGNORECASE).upper()


def find_profile_root(folder: Path) -> Path | None:
    current = folder
    for _ in range(MAX_DEPTH + 1):
        if (current / "index.htm").is_file():
            return current
        children = sorted(p for p in current.iterdir() if p.is_dir() and p.name not in SKIP_NAMES)
        if not children:
            return None
        current = children[0]
    return None


def list_profiles(raw_dir: Path) -> tuple[list[ProfileLocation], list[tuple[int, str]]]:
    """Return the located exports and the (wave, folder code) pairs without an index.htm."""
    found: list[ProfileLocation] = []
    missing: list[tuple[int, str]] = []
    for wave_name, wave in WAVE_DIRS.items():
        wave_dir = raw_dir / wave_name
        if not wave_dir.is_dir():
            continue
        for entry in sorted(wave_dir.iterdir()):
            if not entry.is_dir() or entry.name in SKIP_NAMES:
                continue
            code = folder_code_from_name(entry.name)
            root = find_profile_root(entry)
            if root is None:
                missing.append((wave, code))
            else:
                found.append(ProfileLocation(wave, code, root))
    return found, missing
