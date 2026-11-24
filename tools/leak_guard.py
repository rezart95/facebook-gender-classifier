"""Data-leak guard: refuse files that could carry participant data.

Pre-commit passes the staged file names; CI runs it with --all over every
tracked file. Exit code 1 lists each offending file and the rule it broke.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

MAX_BYTES = 2 * 1024 * 1024
CODE_PATTERN = re.compile(r"\b[A-Z]{2,3}\d{2,5}\b")
PAGE_SUFFIXES = frozenset({".htm", ".html"})
PAGE_ALLOWED = ("pipeline/tests/fixtures/", "web/")
DATA_SUFFIXES = frozenset({".parquet", ".csv", ".dat", ".feather", ".sav"})
DATA_ALLOWED = ("data/synthetic/", "pipeline/src/fbgc_pipeline/features/faithful/data/")
R_DATA_SUFFIXES = frozenset({".rdata", ".rda", ".rds"})
BINARY_SUFFIXES = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".woff2"})
ALLOWLIST_PATH = Path(__file__).with_name("leak_guard_allowlist.txt")
WAVE_DIRS = ("wave1", "wave2")


def folder_code(name: str) -> str:
    return re.sub(r"\.zip$", "", name, flags=re.IGNORECASE).upper()


def load_allowlist(path: Path = ALLOWLIST_PATH) -> set[str]:
    if not path.is_file():
        return set()
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return {line for line in lines if line and not line.startswith("#")}


def load_private_codes(raw_dir: str | None) -> set[str]:
    """Real folder codes, read from the private zone when it exists on this machine."""
    if not raw_dir:
        return set()
    codes: set[str] = set()
    for wave in WAVE_DIRS:
        folder = Path(raw_dir) / wave
        if folder.is_dir():
            codes.update(folder_code(entry.name) for entry in folder.iterdir() if entry.is_dir())
    return codes


def path_problems(rel: str, size: int) -> list[str]:
    suffix = PurePosixPath(rel).suffix.lower()
    problems = []
    if size > MAX_BYTES:
        problems.append("larger than 2 MB")
    if suffix in R_DATA_SUFFIXES:
        problems.append("R data files are never committed")
    if suffix in PAGE_SUFFIXES and not rel.startswith(PAGE_ALLOWED):
        problems.append("HTML pages are only allowed in test fixtures and web/")
    if suffix in DATA_SUFFIXES and not rel.startswith(DATA_ALLOWED):
        problems.append("data files are only allowed in data/synthetic/")
    return problems


def masked(token: str) -> str:
    return token[0] + "*" * (len(token) - 1)


def text_problems(
    text: str, allowlist: set[str], private_codes: set[str], show_tokens: bool
) -> list[str]:
    problems = []
    for token in sorted(set(CODE_PATTERN.findall(text)) - allowlist):
        shown = token if show_tokens else masked(token)
        problems.append(f"looks like a participant code: {shown} (allowlist it if harmless)")
    if any(code in text for code in private_codes):
        problems.append("contains a real folder code")
    return problems


def check_file(
    rel: str, data: bytes, allowlist: set[str], private_codes: set[str], show_tokens: bool
) -> list[str]:
    problems = path_problems(rel, len(data))
    if any(code in rel.upper() for code in private_codes):
        problems.append("file name contains a real folder code")
    if PurePosixPath(rel).suffix.lower() not in BINARY_SUFFIXES:
        text = data.decode("utf-8", errors="replace")
        problems += text_problems(text, allowlist, private_codes, show_tokens)
    return [f"{rel}: {problem}" for problem in problems]


def tracked_files() -> list[str]:
    result = subprocess.run(["git", "ls-files"], check=True, capture_output=True, text=True)
    return [line for line in result.stdout.splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refuse files that could carry participant data.")
    parser.add_argument("files", nargs="*")
    parser.add_argument("--all", action="store_true", help="check every tracked file")
    args = parser.parse_args(argv)
    allowlist = load_allowlist()
    private_codes = load_private_codes(os.environ.get("FBGC_RAW_DIR"))
    show_tokens = not os.environ.get("CI")
    problems: list[str] = []
    for name in tracked_files() if args.all else args.files:
        path = Path(name)
        if path.is_file():
            data = path.read_bytes()
            problems += check_file(path.as_posix(), data, allowlist, private_codes, show_tokens)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
