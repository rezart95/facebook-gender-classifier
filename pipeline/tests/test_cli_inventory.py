import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from fbgc_pipeline.cli import app
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import sample_profile


def test_inventory_counts_exports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = tmp_path / "raw"
    write_fake_export(raw / "wave1" / "alpha.zip", sample_profile())
    write_fake_export(raw / "wave2" / "beta" / "beta", sample_profile(style="en_uk"))
    monkeypatch.setenv("FBGC_RAW_DIR", str(raw))
    monkeypatch.setenv("FBGC_PRIVATE_DIR", str(tmp_path / "private"))
    result = CliRunner().invoke(app, ["inventory"])
    assert result.exit_code == 0, result.output
    summary = json.loads(result.output)
    assert summary["profiles"] == 2
    assert summary["by_language"] == {"it": 1, "en": 1}
    assert summary["pages_present"]["messages.htm"] == 2
    assert (tmp_path / "private" / "inventory.json").is_file()
