import re
from pathlib import Path

from fbgc_pipeline.extract.options import FaithfulOptions
from fbgc_pipeline.extract.profile_extractor import extract_profile
from fbgc_pipeline.locate.profile_finder import ProfileLocation
from fbgc_pipeline.synthetic.fake_export import write_fake_export
from fbgc_pipeline.synthetic.samples import sample_profile
from fbgc_pipeline.validate.calibration_run import profile_counts
from fbgc_pipeline.window.observation import WindowPolicy

ENTRIES = [{"term": "NonLoSo", "phrase": "non lo so", "variant": "substring"}]


def export_without_download_date(root: Path) -> Path:
    write_fake_export(root, sample_profile())
    index = root / "index.htm"
    text = index.read_text(encoding="utf-8")
    index.write_text(
        re.sub(r'<div class="footer">.*?</div>', '<div class="footer">no date</div>', text),
        encoding="utf-8",
        newline="\n",
    )
    return root


def test_windowed_policy_excludes_exports_without_a_download_date(tmp_path: Path) -> None:
    root = export_without_download_date(tmp_path / "alpha")
    for policy in (WindowPolicy.LAST_6_MONTHS, WindowPolicy.LAST_12_MONTHS):
        result = extract_profile(ProfileLocation(1, "ALPHA", root), FaithfulOptions(policy))
        assert (result.status, result.reason) == ("excluded", "no download date")


def test_all_policy_keeps_exports_without_a_download_date(tmp_path: Path) -> None:
    root = export_without_download_date(tmp_path / "alpha")
    result = extract_profile(ProfileLocation(1, "ALPHA", root), FaithfulOptions(WindowPolicy.ALL))
    assert result.status == "ok"


def test_calibration_skips_exports_without_a_download_date(tmp_path: Path) -> None:
    root = export_without_download_date(tmp_path / "alpha")
    location = ProfileLocation(1, "ALPHA", root)
    assert profile_counts(location, ENTRIES, WindowPolicy.LAST_12_MONTHS) == ("ALPHA", None)
    _, counts = profile_counts(location, ENTRIES, WindowPolicy.ALL)
    assert counts is not None
