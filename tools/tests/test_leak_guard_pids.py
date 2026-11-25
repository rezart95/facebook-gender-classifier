"""Leak guard: under data/synthetic/ a participant id (P followed by digits) is refused.

Elsewhere (the demo trace, docstrings) such ids are legitimate, so the rule is folder-scoped.
"""

import importlib.util
import io
from pathlib import Path

import pandas as pd
import pytest

GUARD_PATH = Path(__file__).resolve().parents[1] / "leak_guard.py"
_spec = importlib.util.spec_from_file_location("leak_guard_pids_under_test", GUARD_PATH)
assert _spec is not None and _spec.loader is not None
leak_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(leak_guard)

PID = "P" + "012"


def parquet_bytes(frame: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    frame.to_parquet(buffer, index=False)
    return buffer.getvalue()


def check(rel: str, data: bytes, show_tokens: bool = True) -> list[str]:
    return leak_guard.check_file(rel, data, set(), set(), show_tokens)


def pid_problems(problems: list[str]) -> list[str]:
    return [problem for problem in problems if "participant id" in problem]


def test_a_synthetic_csv_with_a_pid_cell_is_refused() -> None:
    problems = check("data/synthetic/participants.csv", f"pid,wave\n{PID},1\n".encode())
    assert len(pid_problems(problems)) == 1


def test_a_synthetic_parquet_with_a_pid_is_refused() -> None:
    data = parquet_bytes(pd.DataFrame({"pid": [PID], "msg_count": [3.0]}))
    assert len(pid_problems(check("data/synthetic/features.parquet", data))) == 1


def test_a_pid_in_a_synthetic_column_name_is_refused() -> None:
    data = parquet_bytes(pd.DataFrame({PID: [1.0]}))
    assert len(pid_problems(check("data/synthetic/features.parquet", data))) == 1


def test_the_finding_never_names_the_token() -> None:
    problems = check("data/synthetic/participants.csv", f"{PID}\n".encode(), show_tokens=True)
    assert all(PID not in problem for problem in problems)


def test_the_same_parquet_outside_the_synthetic_folder_is_not_refused_for_pids() -> None:
    data = parquet_bytes(pd.DataFrame({"pid": [PID]}))
    assert pid_problems(check("data/demo/features.parquet", data)) == []
    assert check("pipeline/src/x.py", f"# trace of {PID}".encode()) == []


def test_synthetic_ids_pass() -> None:
    data = parquet_bytes(pd.DataFrame({"pid": ["S001", "S012"]}))
    assert check("data/synthetic/features.parquet", data) == []
    assert check("data/synthetic/participants.csv", b"pid\nS001\n") == []


@pytest.mark.parametrize("text", ["X" + PID, PID + "x", "P12", "P0123456abc"])
def test_only_whole_pid_tokens_count(text: str) -> None:
    assert pid_problems(check("data/synthetic/participants.csv", text.encode())) == []


def test_the_pid_check_survives_a_withheld_file_name() -> None:
    rel = "data/synthetic/xycode1.csv"
    problems = leak_guard.check_file(rel, f"{PID}\n".encode(), set(), {"XYCODE1"}, True)
    assert len(pid_problems(problems)) == 1
    assert all(problem.startswith("<file name withheld>") for problem in problems)
