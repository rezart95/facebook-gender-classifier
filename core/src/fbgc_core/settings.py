"""Paths to the private zone and the ID secret, read from FBGC_* environment variables.

The private zone holds the raw exports and anything keyed by real folder codes.
It must never sit inside the repository. The ID secret (FBGC_ID_SECRET) keys the
pseudonymous IDs; it is never written anywhere.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

WORKSPACE_MARKER = "[tool.uv.workspace]"
MIN_SECRET_LENGTH = 32


class PrivateZoneError(ValueError):
    """A private path is missing or sits inside the repository."""


def find_repo_root(start: Path) -> Path:
    resolved = start.resolve()
    for candidate in (resolved, *resolved.parents):
        pyproject = candidate / "pyproject.toml"
        if pyproject.is_file() and WORKSPACE_MARKER in pyproject.read_text(encoding="utf-8"):
            return candidate
    raise PrivateZoneError(f"no workspace root above {start}")


def is_inside(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


class PrivateZone(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FBGC_", hide_input_in_errors=True)

    raw_dir: Path
    private_dir: Path
    id_secret: SecretStr | None = None

    @classmethod
    def from_env(cls) -> PrivateZone:
        return cls()  # pyright: ignore[reportCallIssue]  # fields come from the environment

    def check(self, repo_root: Path) -> None:
        if not self.raw_dir.is_dir():
            raise PrivateZoneError(f"FBGC_RAW_DIR does not exist: {self.raw_dir}")
        for name, path in (("FBGC_RAW_DIR", self.raw_dir), ("FBGC_PRIVATE_DIR", self.private_dir)):
            if is_inside(path, repo_root):
                raise PrivateZoneError(f"{name} must be outside the repository: {path}")

    def require_id_secret(self) -> str:
        if self.id_secret is None:
            raise PrivateZoneError("FBGC_ID_SECRET is not set")
        secret = self.id_secret.get_secret_value()
        if len(secret) < MIN_SECRET_LENGTH:
            raise PrivateZoneError(
                f"FBGC_ID_SECRET must have at least {MIN_SECRET_LENGTH} characters"
            )
        return secret
