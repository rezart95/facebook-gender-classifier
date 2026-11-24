"""Leak guard: the binary check survives a withheld name; Parquet files are scanned by content.

Code-shaped strings are assembled at runtime so this file never contains one literally.
"""

import importlib.util
import io
from pathlib import Path

import pandas as pd

GUARD_PATH = Path(__file__).resolve().parents[1] / "leak_guard.py"
_spec = importlib.util.spec_from_file_location("leak_guard_scan_under_test", GUARD_PATH)
assert _spec is not None and _spec.loader is not None
leak_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(leak_guard)

FAKE_CODE = "QZ" + "98765"
REAL_CODE = "XY" + "CODE1"


def parquet_bytes(frame: pd.DataFrame, plain: bool = False) -> bytes:
    buffer = io.BytesIO()
    if plain:  # no compression and no dictionary: values keep their raw bytes
        frame.to_parquet(buffer, index=False, compression=None, use_dictionary=False)
    else:
        frame.to_parquet(buffer, index=False)
    return buffer.getvalue()


def check(rel: str, data: bytes, codes: set[str] | None = None) -> list[str]:
    return leak_guard.check_file(rel, data, set(), codes or set(), True)


def test_binary_file_with_a_withheld_name_still_skips_the_text_scan() -> None:
    rel = f"docs/{REAL_CODE.lower()}-figure.png"
    problems = check(rel, REAL_CODE.encode(), codes={REAL_CODE})
    assert problems == ["<file name withheld>: file name contains a real folder code"]


def test_numeric_parquet_passes_even_when_its_bytes_spell_a_code() -> None:
    value = int.from_bytes(b" " + FAKE_CODE[:6].encode() + b" ", "little")
    data = parquet_bytes(pd.DataFrame({"n": [value]}), plain=True)
    assert FAKE_CODE[:6].encode() in data  # the raw bytes would fool a plain text scan
    assert check("data/synthetic/features.parquet", data) == []


def test_parquet_string_cells_are_scanned() -> None:
    data = parquet_bytes(pd.DataFrame({"pid": ["S001", FAKE_CODE], "x": [1.0, 2.0]}))
    problems = check("data/synthetic/features.parquet", data)
    assert len(problems) == 1
    assert FAKE_CODE in problems[0]


def test_parquet_column_names_are_scanned() -> None:
    data = parquet_bytes(pd.DataFrame({f"value_{FAKE_CODE}": [1.0]}))
    assert len(check("data/synthetic/features.parquet", data)) == 1


def test_parquet_real_codes_are_found_in_any_case() -> None:
    data = parquet_bytes(pd.DataFrame({"pid": [REAL_CODE.lower()]}))
    problems = check("data/synthetic/features.parquet", data, codes={REAL_CODE})
    assert problems == ["data/synthetic/features.parquet: contains a real folder code"]


def test_unreadable_parquet_is_a_problem() -> None:
    problems = check("data/synthetic/features.parquet", b"not a parquet file")
    assert problems == ["data/synthetic/features.parquet: unreadable Parquet file"]
