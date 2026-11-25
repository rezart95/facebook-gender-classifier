import pytest
from typer.testing import CliRunner

from fbgc_pipeline.cli import app
from fbgc_pipeline.load.database_load import is_local_database

REFUSED = [
    "postgresql+psycopg://u:p@/fbgc?host=db.example.org",
    "postgresql+psycopg://u:p@localhost/fbgc?host=db.example.org",
    "postgresql+psycopg://u:p@localhost/fbgc?hostaddr=8.8.8.8",
    "postgresql+psycopg://u:p@localhost/fbgc?service=x",
    "postgresql+psycopg://u:p@localhost/fbgc?HOSTADDR=8.8.8.8",
    "postgresql+psycopg://u:p@localhost/fbgc?servicefile=/tmp/s",
    "postgresql+psycopg://u:p@localhost/fbgc?passfile=/tmp/p",
    "postgresql+psycopg://u:p@/fbgc",
    "postgresql+psycopg://u:p@db.example.org/fbgc",
    "postgresql+psycopg://u:p@LOCALHOST.example.org/fbgc",
]
ACCEPTED = [
    "postgresql+psycopg://u:p@localhost/fbgc",
    "postgresql+psycopg://u:p@127.0.0.1:5433/fbgc",
    "postgresql+psycopg://u:p@[::1]/fbgc",
    "sqlite:///x.db",
    "sqlite://",
]


@pytest.mark.parametrize("url", REFUSED)
def test_gate_refuses(url: str) -> None:
    assert not is_local_database(url)


@pytest.mark.parametrize("url", ACCEPTED)
def test_gate_accepts(url: str) -> None:
    assert is_local_database(url)


@pytest.mark.parametrize("variable", ["PGHOSTADDR", "PGSERVICE"])
def test_private_refused_when_libpq_environment_redirects(
    monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    monkeypatch.setenv(variable, "somewhere")
    url = "postgresql+psycopg://u:p@localhost/fbgc"
    result = CliRunner().invoke(app, ["load", "--private", "--database-url", url])
    assert result.exit_code == 1
    assert "local database" in result.output


def test_malformed_url_is_refused_without_echo() -> None:
    url = "postgresql+psycopg://u:x@localhost:p@db.example.org/fbgc"
    result = CliRunner().invoke(app, ["load", "--synthetic", "--database-url", url])
    assert result.exit_code == 1
    assert result.output.strip() == "the database URL is not valid"
    assert "db.example.org" not in result.output
    assert "u:x" not in result.output
