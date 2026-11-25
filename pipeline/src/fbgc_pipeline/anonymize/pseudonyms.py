"""Pseudonymous participant IDs: P001..Pnnn, ranked by HMAC-SHA256 over (wave, folder code).

The ranking needs the secret, so the IDs are stable across runs yet cannot be mapped back
without it. No mapping file is ever written; the secret stays in memory.
"""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Sequence


def pid_key(wave: int, folder_code: str) -> str:
    return f"{int(wave)}:{folder_code}"


def pseudonymous_ids(keys: Sequence[str], secret: str) -> list[str]:
    """One ID per key, in the order of `keys`; P001 goes to the smallest digest."""
    digests = [
        hmac.new(secret.encode("utf-8"), key.encode("utf-8"), hashlib.sha256).hexdigest()
        for key in keys
    ]
    if len(set(digests)) != len(digests):
        raise ValueError("profile keys must be unique")
    width = max(3, len(str(len(keys))))
    ids = [""] * len(keys)
    for rank, index in enumerate(sorted(range(len(keys)), key=digests.__getitem__), start=1):
        ids[index] = f"P{rank:0{width}d}"
    return ids
