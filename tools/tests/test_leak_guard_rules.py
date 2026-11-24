"""More leak-guard rules: file-name codes, blocked data types, local-only docs, warning.

Code-shaped strings are assembled at runtime so this file never contains one literally.
"""

import importlib.util
from pathlib import Path

import pytest

from fbgc_pipeline.locate.profile_finder import folder_code_from_name

GUARD_PATH = Path(__file__).resolve().parents[1] / "leak_guard.py"
_spec = importlib.util.spec_from_file_location("leak_guard_rules_under_test", GUARD_PATH)
assert _spec is not None and _spec.loader is not None
leak_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(leak_guard)

FAKE_CODE = "QZ" + "98765"
SUFFIXES = [".zip", ".xlsx", ".xls", ".pkl", ".pickle", ".npy", ".npz"]
SUFFIXES += [".sqlite", ".db", ".sql", ".tsv", ".jsonl"]


def check(rel: str, text: str = "", allow: set[str] | None = None) -> list[str]:
    return leak_guard.check_file(rel, text.encode(), allow or set(), set(), True)


def test_missing_raw_dir_warns_and_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("FBGC_RAW_DIR", str(tmp_path / "missing"))
    (tmp_path / "good.md").write_text("hello", encoding="utf-8")
    assert leak_guard.main(["good.md"]) == 0
    assert capsys.readouterr().err.count(leak_guard.OFF_WARNING) == 1


def test_no_warning_when_codes_are_known_or_in_ci(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "raw" / "wave1" / "xycode1").mkdir(parents=True)
    (tmp_path / "good.md").write_text("hello", encoding="utf-8")
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("FBGC_RAW_DIR", str(tmp_path / "raw"))
    assert leak_guard.main(["good.md"]) == 0
    assert capsys.readouterr().err == ""
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("FBGC_RAW_DIR")
    assert leak_guard.main(["good.md"]) == 0
    assert capsys.readouterr().err == ""


def test_code_shaped_file_names_are_rejected_locally_with_the_token() -> None:
    problems = check(f"docs/notes_{FAKE_CODE}.md")
    reason = f"file name looks like a participant code: {FAKE_CODE}"
    assert problems == [f"docs/notes_{FAKE_CODE}.md: {reason}"]


def test_code_shaped_file_names_are_withheld_in_ci() -> None:
    data = b""
    problems = leak_guard.check_file(f"docs/{FAKE_CODE}.md", data, set(), set(), False)
    assert problems == ["<file name withheld>: file name looks like a participant code"]
    assert not any(FAKE_CODE in problem for problem in problems)


def test_allowlisted_file_name_token_passes() -> None:
    assert check(f"docs/{FAKE_CODE}.md", allow={FAKE_CODE}) == []


@pytest.mark.parametrize("suffix", SUFFIXES)
def test_more_data_types_are_blocked_outside_synthetic_folders(suffix: str) -> None:
    assert check(f"data/real{suffix}") != []
    assert check(f"data/synthetic/sample{suffix}") == []
    faithful = "pipeline/src/fbgc_pipeline/features/faithful/data/"
    assert check(f"{faithful}words{suffix}") == []


def test_docs_superpowers_is_never_tracked() -> None:
    problems = check("docs/superpowers/plans/plan.md", "planning")
    reason = "planning docs under docs/superpowers/ are local only"
    assert problems == [f"docs/superpowers/plans/plan.md: {reason}"]


def test_private_codes_skip_junk_and_dot_folders(tmp_path: Path) -> None:
    for name in ("xycode1.zip", "__MACOSX", ".DS_Store", ".directory", ".hidden"):
        (tmp_path / "wave1" / name).mkdir(parents=True)
    assert leak_guard.load_private_codes(str(tmp_path)) == {"XYCODE1"}


@pytest.mark.parametrize("name", ["abc.zip", "ABC.ZIP", "abc", "Ab9.Zip", "x.zip.zip"])
def test_folder_code_agrees_with_the_pipeline(name: str) -> None:
    assert leak_guard.folder_code(name) == folder_code_from_name(name)
