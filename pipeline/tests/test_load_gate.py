from pathlib import Path

import pytest
from typer.testing import CliRunner

from fbgc_pipeline.cli import app
from fbgc_pipeline.cli.common import repo_root
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
    "mysql://u:p@localhost/x",
    "mssql+pyodbc://u:p@localhost/x",
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


def test_private_refuses_a_redirected_postgres_url() -> None:
    url = "postgresql+psycopg://u:p@localhost/fbgc?host=db.example.org"
    result = CliRunner().invoke(app, ["load", "--private", "--database-url", url])
    assert result.exit_code == 1
    assert "local database" in result.output
    assert "db.example.org" not in result.output


def test_private_refuses_a_sqlite_file_inside_the_repo() -> None:
    inside = repo_root() / "never-created-folder" / "private.sqlite"
    result = CliRunner().invoke(
        app, ["load", "--private", "--database-url", f"sqlite:///{inside.as_posix()}"]
    )
    assert result.exit_code == 1
    assert result.output.strip() == "private data must not be written inside the repository"
    assert not inside.parent.exists()


def test_private_refuses_a_relative_sqlite_path_inside_the_repo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(repo_root())
    result = CliRunner().invoke(
        app, ["load", "--private", "--database-url", "sqlite:///never-created.sqlite"]
    )
    assert result.exit_code == 1
    assert "inside the repository" in result.output
    assert not (repo_root() / "never-created.sqlite").exists()


def test_private_allows_in_memory_and_outside_sqlite(tmp_path: Path) -> None:
    """The refusal is not the repo one: the load goes on and stops at the missing inputs."""
    for url in ("sqlite://", f"sqlite:///{(tmp_path / 'x.sqlite').as_posix()}"):
        args = ["load", "--private", "--database-url", url, "--from", str(tmp_path / "none")]
        result = CliRunner().invoke(app, args)
        assert "inside the repository" not in result.output
        assert "missing input files" in result.output
