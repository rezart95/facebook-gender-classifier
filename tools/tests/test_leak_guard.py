"""Tests for the data-leak guard.

Code-shaped strings are assembled at runtime so this file never contains one literally.
"""

import importlib.util
from pathlib import Path

import pytest

GUARD_PATH = Path(__file__).resolve().parents[1] / "leak_guard.py"
_spec = importlib.util.spec_from_file_location("leak_guard", GUARD_PATH)
assert _spec is not None and _spec.loader is not None
leak_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(leak_guard)

FAKE_CODE = "QZ" + "98765"


def check(
    rel: str, text: str = "", allow: set[str] | None = None, codes: set[str] | None = None
) -> list[str]:
    return leak_guard.check_file(rel, text.encode(), allow or set(), codes or set(), True)


def test_clean_source_file_passes() -> None:
    assert check("core/src/fbgc_core/x.py", "print('hello')") == []


def test_code_like_token_is_rejected() -> None:
    problems = check("docs/notes.md", f"participant {FAKE_CODE} wrote")
    assert len(problems) == 1
    assert FAKE_CODE in problems[0]


def test_allowlisted_token_passes() -> None:
    token = "ISO" + "8601"
    assert check("docs/notes.md", f"dates in {token}", allow={token}) == []


def test_tokens_are_masked_when_running_in_ci() -> None:
    problems = leak_guard.check_file("docs/notes.md", FAKE_CODE.encode(), set(), set(), False)
    assert FAKE_CODE not in problems[0]
    assert FAKE_CODE[0] + "*" * (len(FAKE_CODE) - 1) in problems[0]


def test_real_folder_code_is_rejected_without_being_printed() -> None:
    problems = check("docs/notes.md", "SEE XYCODE1 HERE", codes={"XYCODE1"})
    assert problems == ["docs/notes.md: contains a real folder code"]


def test_file_name_with_real_code_is_rejected() -> None:
    problems = check("docs/xycode1-notes.md", "", codes={"XYCODE1"})
    assert problems == ["<file name withheld>: file name contains a real folder code"]


def test_real_folder_code_is_rejected_in_lowercase() -> None:
    problems = check("docs/notes.md", "see xycode1 here", codes={"XYCODE1"})
    assert problems == ["docs/notes.md: contains a real folder code"]


@pytest.mark.parametrize(
    "text", [f"features_{FAKE_CODE}.csv", f"{FAKE_CODE}_x", f"a_{FAKE_CODE}_b"]
)
def test_code_next_to_underscore_is_rejected(text: str) -> None:
    assert len(check("docs/notes.md", text)) == 1


def test_code_glued_to_letters_or_digits_is_not_a_code() -> None:
    assert check("docs/notes.md", f"a{FAKE_CODE} {FAKE_CODE}9 {FAKE_CODE}b") == []


def test_ls_files_output_is_split_on_nul() -> None:
    names = leak_guard.split_ls_files("a.md\0d\u00e9j\u00e0/vu.md\0")
    assert names == ["a.md", "d\u00e9j\u00e0/vu.md"]
    assert leak_guard.split_ls_files("") == []


def test_r_data_files_are_rejected() -> None:
    assert "R data files" in check("anything/dati.RData")[0]


def test_html_pages_only_in_fixtures() -> None:
    assert check("docs/messages.htm") != []
    assert check("pipeline/tests/fixtures/profiles/a/index.htm") == []


def test_data_files_only_in_synthetic_folder() -> None:
    assert check("data/real.csv") != []
    assert check("data/synthetic/features.csv") == []


def test_large_files_are_rejected() -> None:
    data = b"x" * (leak_guard.MAX_BYTES + 1)
    problems = leak_guard.check_file("docs/big.txt", data, set(), set(), True)
    assert "larger than 2 MB" in problems[0]


def test_binary_files_skip_the_text_scan() -> None:
    assert check("docs/thesis/figure.png", FAKE_CODE) == []


def test_private_codes_come_from_wave_folders(tmp_path: Path) -> None:
    (tmp_path / "wave1" / "xycode1.zip").mkdir(parents=True)
    (tmp_path / "wave2" / "xycode2").mkdir(parents=True)
    assert leak_guard.load_private_codes(str(tmp_path)) == {"XYCODE1", "XYCODE2"}
    assert leak_guard.load_private_codes(None) == set()


def test_main_reports_bad_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FBGC_RAW_DIR", raising=False)
    (tmp_path / "good.md").write_text("hello", encoding="utf-8")
    (tmp_path / "bad.md").write_text(FAKE_CODE, encoding="utf-8")
    assert leak_guard.main(["good.md"]) == 0
    assert leak_guard.main(["bad.md"]) == 1
    assert "bad.md" in capsys.readouterr().err
