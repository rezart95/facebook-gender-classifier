import json
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from fbgc_pipeline.anonymize.age_bands import ALL_AGE_BANDS
from fbgc_pipeline.anonymize.tables import anonymize_profiles
from fbgc_pipeline.cli import app
from fbgc_pipeline.cli.common import repo_root
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.fake_export_html import FAKE_MARKER
from fbgc_pipeline.synthetic.samples import sample_profile
from fbgc_pipeline.trace.recorder import NotAFakeProfileError, record_trace
from fbgc_pipeline.trace.stages import DEMO_SECRET, TRACE_FEATURES

FAKE_01 = Path(__file__).with_name("fixtures") / "profiles" / "fake-01"
STAGES = ["raw_html", "parsed_messages", "owner_split", "dictionary_hits", "features", "anonymized"]


def stage(trace: dict[str, object], name: str) -> dict[str, object]:
    stages = trace["stages"]
    assert isinstance(stages, list)
    return next(item for item in stages if item["stage"] == name)


def test_trace_records_every_stage_in_order() -> None:
    trace = record_trace(FAKE_01, "fake-01")
    assert trace["fake"] is True
    assert [item["stage"] for item in trace["stages"]] == STAGES
    snippet = stage(trace, "raw_html")["snippet"]
    assert isinstance(snippet, str) and snippet.startswith('<div class="thread">')
    assert snippet.endswith(">")
    messages = stage(trace, "parsed_messages")["messages"]
    assert isinstance(messages, list) and len(messages) == 10


def test_trace_shows_the_owner_split_hits_and_features() -> None:
    trace = record_trace(FAKE_01, "fake-01")
    split = stage(trace, "owner_split")
    assert isinstance(split["owner"], str) and split["owner_messages"] > 0
    assert stage(trace, "dictionary_hits")["hits"]
    assert list(stage(trace, "features")["values"]) == list(TRACE_FEATURES)


def test_the_anonymized_row_is_coarse() -> None:
    anonymized = stage(record_trace(FAKE_01, "fake-01"), "anonymized")
    person = anonymized["participant"]
    assert isinstance(person, dict)
    assert (person["pid"], person["gender"]) == ("P001", "F")
    assert person["age_band"] in ALL_AGE_BANDS
    friends = anonymized["features"]["friends_accepted"]
    assert friends % 10 == 0


def test_the_anonymized_stage_records_its_demo_k() -> None:
    assert stage(record_trace(FAKE_01, "fake-01"), "anonymized")["k"] == 1


def test_the_privacy_floor_still_refuses_k_of_one() -> None:
    frame = pd.DataFrame([{"wave": 1, "folder_code": "alpha", "status": "ok", "gender": "F"}])
    with pytest.raises(ValueError, match="k"):
        anonymize_profiles(frame, [], DEMO_SECRET, k=1)


def test_traces_are_deterministic_json_without_nan() -> None:
    first, second = record_trace(FAKE_01, "fake-01"), record_trace(FAKE_01, "fake-01")
    assert json.dumps(first, allow_nan=False) == json.dumps(second, allow_nan=False)


def test_the_committed_demo_trace_is_current() -> None:
    committed = repo_root() / "data" / "demo" / "trace-fake-01.json"
    fresh = json.loads(json.dumps(record_trace(FAKE_01, "fake-01"), default=str))
    assert json.loads(committed.read_text(encoding="utf-8")) == fresh


def test_exports_without_the_fake_marker_are_refused(tmp_path: Path) -> None:
    root = write_fake_export(tmp_path / "alpha", sample_profile())
    index = root / "index.htm"
    index.write_text(index.read_text(encoding="utf-8").replace(FAKE_MARKER, "x"), encoding="utf-8")
    with pytest.raises(NotAFakeProfileError):
        record_trace(root, "alpha")


def test_cli_trace(tmp_path: Path) -> None:
    out = tmp_path / "trace.json"
    result = CliRunner().invoke(app, ["trace", "--profile", str(FAKE_01), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert json.loads(out.read_text(encoding="utf-8"))["profile_label"] == "fake-01"
    refused = CliRunner().invoke(app, ["trace", "--profile", str(tmp_path), "--out", str(out)])
    assert refused.exit_code == 1
    assert "fake profiles only" in refused.output
