from pathlib import Path

from lxml import etree

from fbgc_pipeline.parse.html_loading import clean_text, find_all, full_text, load_tree

WALL = (
    '<html><body><div class="contents"><div><p><div class="meta">t</div>{action}</p></div></div>'
    "</body></html>"
)


def test_strict_xml_keeps_div_inside_p(tmp_path: Path) -> None:
    page = tmp_path / "wall.htm"
    page.write_text(WALL.format(action="ok"), encoding="utf-8")
    assert len(find_all(load_tree(page, keep_nesting=True), "//p/div[@class='meta']")) == 1


def test_broken_page_keeps_nesting_when_asked(tmp_path: Path) -> None:
    page = tmp_path / "wall.htm"
    page.write_text(WALL.format(action="a & b"), encoding="utf-8")
    assert len(find_all(load_tree(page, keep_nesting=True), "//p/div[@class='meta']")) == 1


def test_broken_page_falls_back_to_html(tmp_path: Path) -> None:
    page = tmp_path / "messages.htm"
    page.write_text(
        '<html><body><div class="thread">A, B<p>pane & vino&nbsp;!</p></div></body></html>',
        encoding="utf-8",
    )
    paragraph = find_all(load_tree(page, keep_nesting=False), "//p")[0]
    assert full_text(paragraph).startswith("pane & vino")


def test_clean_text_normalises_whitespace() -> None:
    node = etree.fromstring("<p>  Giulia \n  <b>Bianchi</b>  </p>")
    assert clean_text(node) == "Giulia Bianchi"
    assert clean_text(None) == ""
