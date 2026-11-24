import math
from pathlib import Path

import pandas as pd
import pyreadr
import pytest

from fbgc_core.catalogue import default_catalogue
from fbgc_pipeline.survey.scales import (
    SurveyColumnsError,
    join_survey,
    load_survey_scores,
    survey_columns,
    survey_scores,
)


def scale_frame() -> pd.DataFrame:
    """A tiny scale file: 'alpha' appears twice (as in the real file), 'gamma' has no scores."""
    rows: dict[str, list[object]] = {"CODICE.ZIP": ["alpha.zip", "beta", "ALPHA", "gamma"]}
    for index, legacy in enumerate(survey_columns(default_catalogue())):
        rows[legacy] = [1.0 + index % 3, 2.0, 3.0 + index % 3, math.nan]
    rows["z1"] = [20.0, 21.0, 22.0, 23.0]
    return pd.DataFrame(rows)


def test_survey_columns_cover_the_38_scales() -> None:
    columns = survey_columns(default_catalogue())
    assert len(columns) == 38
    assert columns["H_extraversion"] == "big5_extraversion"
    assert columns["autostima"] == "self_esteem"


def test_load_survey_scores_from_rdata(tmp_path: Path) -> None:
    path = tmp_path / "scales.Rdata"
    pyreadr.write_rdata(str(path), scale_frame(), df_name="dati")
    scores = load_survey_scores(path, default_catalogue())
    assert list(scores.index) == ["ALPHA", "BETA", "GAMMA"]
    assert scores.shape == (3, 38)
    assert scores.loc["ALPHA", "gpius_posi"] == 2.0  # (1 + 3) / 2: duplicates are averaged
    assert scores.loc["BETA", "self_esteem"] == 2.0
    assert scores.loc["GAMMA"].isna().all()
    assert "z1" not in scores.columns
    assert set(scores.dtypes.astype(str)) == {"float64"}


def test_missing_scale_columns_are_named_without_demographics() -> None:
    frame = scale_frame().drop(columns=["F_posi", "M_csc"])
    with pytest.raises(SurveyColumnsError, match=r"\['F_posi', 'M_csc'\]") as error:
        survey_scores(frame, default_catalogue())
    assert "z1" not in str(error.value)
    assert "CODICE.ZIP" not in str(error.value)


def test_join_survey_adds_scores_and_has_survey() -> None:
    scores = survey_scores(scale_frame(), default_catalogue())
    profiles = pd.DataFrame(
        {"wave": [1, 2, 2], "folder_code": ["ALPHA", "DELTA", "GAMMA"], "msg_count": [5.0, 6, 7]}
    )
    joined = join_survey(profiles, scores)
    assert list(joined["has_survey"]) == [True, False, False]
    assert joined.loc[0, "gpius_posi"] == 2.0
    assert math.isnan(joined.loc[1, "gpius_posi"])
    assert list(joined["msg_count"]) == [5.0, 6.0, 7.0]
    assert list(joined["folder_code"]) == ["ALPHA", "DELTA", "GAMMA"]
