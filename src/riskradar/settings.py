"""Application settings: environment variables + configs/config.yaml."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mlflow_tracking_uri: str = f"sqlite:///{REPO_ROOT / 'mlflow.db'}"
    config_path: Path = REPO_ROOT / "configs" / "config.yaml"


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


@functools.lru_cache(maxsize=1)
def get_config() -> dict[str, Any]:
    with open(get_settings().config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_path(relative: str | Path) -> Path:
    p = Path(relative)
    return p if p.is_absolute() else REPO_ROOT / p
