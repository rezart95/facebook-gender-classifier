"""Leak guard: the binary check survives a withheld name; Parquet files are scanned by content.

Code-shaped strings are assembled at runtime so this file never contains one literally.
"""

import importlib.util
import io
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

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


def table_bytes(table: pa.Table) -> bytes:
    buffer = io.BytesIO()
    pq.write_table(table, buffer)
    return buffer.getvalue()


def test_nested_list_cells_are_scanned() -> None:
    data = table_bytes(pa.table({"tags": pa.array([["ok", FAKE_CODE]], pa.list_(pa.string()))}))
    problems = check("data/synthetic/features.parquet", data)
    assert len(problems) == 1 and FAKE_CODE in problems[0]


def test_struct_field_names_are_scanned() -> None:
    data = table_bytes(pa.table({"s": pa.array([{f"f_{FAKE_CODE}": 1}])}))
    problems = check("data/synthetic/features.parquet", data)
    assert len(problems) == 1 and FAKE_CODE in problems[0]


def test_map_keys_and_values_are_scanned() -> None:
    map_type = pa.map_(pa.string(), pa.string())
    for pair in ([(FAKE_CODE, "v")], [("k", FAKE_CODE)]):
        data = table_bytes(pa.table({"m": pa.array([pair], map_type)}))
        assert len(check("data/synthetic/features.parquet", data)) == 1


def test_schema_metadata_values_are_scanned() -> None:
    table = pa.table({"n": [1.0]}).replace_schema_metadata({"note": FAKE_CODE})
    problems = check("data/synthetic/features.parquet", table_bytes(table))
    assert len(problems) == 1 and FAKE_CODE in problems[0]


def test_field_metadata_is_scanned() -> None:
    field = pa.field("n", pa.float64(), metadata={FAKE_CODE: "x"})
    data = table_bytes(pa.table({"n": [1.0]}, schema=pa.schema([field])))
    assert len(check("data/synthetic/features.parquet", data)) == 1


def test_binary_cells_are_decoded_and_scanned() -> None:
    data = table_bytes(pa.table({"b": pa.array([FAKE_CODE.encode()], pa.binary())}))
    problems = check("data/synthetic/features.parquet", data)
    assert len(problems) == 1 and FAKE_CODE in problems[0]


def test_unused_dictionary_categories_are_scanned() -> None:
    column = pa.DictionaryArray.from_arrays(pa.array([0, 0], pa.int8()), ["ok", FAKE_CODE])
    data = table_bytes(pa.table({"c": column}))
    problems = check("data/synthetic/features.parquet", data)
    assert len(problems) == 1 and FAKE_CODE in problems[0]


def test_real_codes_inside_nested_cells_are_found() -> None:
    cell = [{"inner": [REAL_CODE.lower()]}]
    data = table_bytes(pa.table({"s": pa.array(cell)}))
    problems = check("data/synthetic/features.parquet", data, codes={REAL_CODE})
    assert problems == ["data/synthetic/features.parquet: contains a real folder code"]


def test_odd_parquet_content_is_unreadable_not_a_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_: object) -> None:
        raise ValueError("hostile file")

    monkeypatch.setattr(pq, "read_table", boom)
    problems = check("data/synthetic/features.parquet", b"PAR1")
    assert problems == ["data/synthetic/features.parquet: unreadable Parquet file"]
