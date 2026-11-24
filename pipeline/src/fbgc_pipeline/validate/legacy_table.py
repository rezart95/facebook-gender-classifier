"""Read the 2019 R data files (private zone). Only the feature table and the gender label are used.

dati_info.RData also holds names, e-mails, birth dates and hometowns: only the code and
gender columns are kept, and nothing from it is ever written out.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadr

LEGACY_CODE_COLUMN = "CODICE.ZIP"


def _first_frame(path: Path) -> pd.DataFrame:
    return next(iter(pyreadr.read_r(str(path)).values()))


def normalise_codes(codes: pd.Series) -> pd.Series:
    return codes.astype(str).str.strip().str.upper().str.replace(r"\.ZIP$", "", regex=True)


def load_legacy_features(path: Path) -> pd.DataFrame:
    """The 2019 features indexed by folder code; codes appearing twice are dropped as ambiguous."""
    frame = _first_frame(path)
    frame = frame.assign(folder_code=normalise_codes(frame[LEGACY_CODE_COLUMN]))
    frame = frame.drop(columns=[LEGACY_CODE_COLUMN]).drop_duplicates("folder_code", keep=False)
    return frame.set_index("folder_code")


def load_legacy_gender(path: Path) -> pd.Series:
    frame = _first_frame(path)[[LEGACY_CODE_COLUMN, "sesso"]]
    frame = frame.assign(folder_code=normalise_codes(frame[LEGACY_CODE_COLUMN]))
    frame = frame.drop_duplicates("folder_code", keep=False)
    return frame.set_index("folder_code")["sesso"].astype(str)
