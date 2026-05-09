from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


@lru_cache(maxsize=1)
def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@lru_cache(maxsize=1)
def get_repo_env_path() -> Path:
    return get_repo_root() / ".env.local"


@lru_cache(maxsize=1)
def load_repo_env() -> Path:
    repo_root = get_repo_root()
    loaded_path = get_repo_env_path()

    for candidate in (repo_root / ".env.local", repo_root / ".env"):
        if candidate.exists():
            load_dotenv(candidate, override=False)
            loaded_path = candidate

    return loaded_path
