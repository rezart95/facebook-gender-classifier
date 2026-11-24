"""What the leak guard looks for inside a file, and which part of the file it reads.

Parquet bytes are compressed numbers that can spell a code-shaped token by chance, so a
Parquet file is opened and only its column names and string cells are scanned.
"""

from __future__ import annotations

import io
import re
from collections.abc import Iterator
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

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


def _decoded(blob: bytes) -> str:
    return blob.decode("utf-8", errors="replace")


def _value_texts(value: Any) -> Iterator[str]:
    """Every string in a cell, however deeply it is nested; bytes are decoded."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, bytes):
        yield _decoded(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _value_texts(key)
            yield from _value_texts(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _value_texts(item)


def _metadata_texts(metadata: dict[bytes, bytes] | None) -> Iterator[str]:
    for key, value in (metadata or {}).items():
        yield _decoded(key)
        yield _decoded(value)


def _field_texts(field: Any) -> Iterator[str]:
    """A field's name and metadata, then those of every nested field."""
    yield field.name
    yield from _metadata_texts(field.metadata)
    data_type = field.type
    if pa.types.is_dictionary(data_type):
        data_type = data_type.value_type
    for index in range(data_type.num_fields):
        yield from _field_texts(data_type.field(index))


def _array_texts(array: Any) -> Iterator[str]:
    """Strings of an array, including dictionary entries that no row references."""
    yield from _value_texts(array.to_pylist())
    data_type = array.type
    if pa.types.is_dictionary(data_type):
        yield from _array_texts(array.dictionary)
    elif pa.types.is_struct(data_type):
        for child in array.flatten():
            yield from _array_texts(child)


def parquet_strings(data: bytes) -> str | None:
    """Every piece of text in a Parquet file, or None when it cannot be read.

    That is: column and nested field names, schema and field metadata, string and binary
    cells at any depth, and dictionary entries.
    """
    try:
        table = pq.read_table(io.BytesIO(data))
        texts = [*_metadata_texts(table.schema.metadata)]
        for field in table.schema:
            texts.extend(_field_texts(field))
        for column in table.columns:
            for chunk in column.chunks:
                texts.extend(_array_texts(chunk))
    except Exception:  # a hostile or odd file must be reported, not crash the whole run
        return None
    return "\n".join(texts)


def scannable_text(suffix: str, data: bytes) -> str | None:
    """Text to scan for codes: '' for binary files, None for an unreadable Parquet file."""
    if suffix in BINARY_SUFFIXES:
        return ""
    if suffix == PARQUET_SUFFIX:
        return parquet_strings(data)
    return data.decode("utf-8", errors="replace")
