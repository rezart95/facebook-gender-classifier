"""What the leak guard looks for inside a file, and which part of the file it reads.

Parquet bytes are compressed numbers that can spell a code-shaped token by chance, so a
Parquet file is opened and only its column names and string cells are scanned.
"""

from __future__ import annotations

import io
import re

CODE_PATTERN = re.compile(r"(?<![A-Za-z0-9])[A-Z]{2,3}\d{2,5}(?![A-Za-z0-9])")
BINARY_SUFFIXES = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".woff2"})
PARQUET_SUFFIX = ".parquet"


def masked(token: str) -> str:
    return token[0] + "*" * (len(token) - 1)


def text_problems(
    text: str, allowlist: set[str], private_codes: set[str], show_tokens: bool
) -> list[str]:
    problems = []
    for token in sorted(set(CODE_PATTERN.findall(text)) - allowlist):
        shown = token if show_tokens else masked(token)
        problems.append(f"looks like a participant code: {shown} (allowlist it if harmless)")
    upper_text = text.upper()
    if any(code in upper_text for code in private_codes):
        problems.append("contains a real folder code")
    return problems


def parquet_strings(data: bytes) -> str | None:
    """Column names and string cells of a Parquet file, or None when it cannot be read."""
    import pyarrow as pa  # imported here: only Parquet files need it
    import pyarrow.parquet as pq

    try:
        table = pq.read_table(io.BytesIO(data))
    except (pa.ArrowException, OSError):
        return None
    cells = (cell for column in table.columns for cell in column.to_pylist())
    return "\n".join([*table.column_names, *(cell for cell in cells if isinstance(cell, str))])


def scannable_text(suffix: str, data: bytes) -> str | None:
    """Text to scan for codes: '' for binary files, None for an unreadable Parquet file."""
    if suffix in BINARY_SUFFIXES:
        return ""
    if suffix == PARQUET_SUFFIX:
        return parquet_strings(data)
    return data.decode("utf-8", errors="replace")
