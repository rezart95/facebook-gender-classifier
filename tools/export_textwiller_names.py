"""One-off: export TextWiller's vocabolarioNomiPropri to CSV.

TextWiller (Livio Finos and contributors) is GPL >= 2. The list holds generic first names
and organisation markers; it contains no participant data.
Usage: python tools/export_textwiller_names.py <vocabolarioNomiPropri.rda> <out.csv>
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pyreadr


def main(rda_path: str, out_path: str) -> None:
    frame = pyreadr.read_r(rda_path)["vocabolarioNomiPropri"]
    rows = sorted((str(name), str(category)) for name, category in frame["categoria"].items())
    with Path(out_path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["name", "category"])
        writer.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
