from __future__ import annotations

import getpass
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import dotenv_values, set_key

from packages.shared.python.ai_court_shared.env_config import (
    get_repo_env_path,
    load_repo_env,
)

PROVIDER_OPTIONS = [
    "auto",
    "openrouter",
    "groq",
    "deepseek",
    "nvidia",
    "9router",
    "ollama",
    "heuristic",
]

CONFIG_SECTIONS: dict[str, dict[str, str]] = {
    "openrouter": {
        "OPENROUTER_API_KEY": "",
        "OPENROUTER_MODEL": "inclusionai/ring-2.6-1t:free",
        "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    },
    "groq": {
        "GROQ_API_KEY": "",
        "GROQ_MODEL": "qwen/qwen3-32b",
        "GROQ_BASE_URL": "https://api.groq.com/openai/v1",
    },
    "deepseek": {
        "DEEPSEEK_API_KEY": "",
        "DEEPSEEK_MODEL": "deepseek-v4-pro",
        "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
    },
    "nvidia": {
        "NVIDIA_API_KEY": "",
        "NVIDIA_MODEL": "z-ai/glm4.7",
        "NVIDIA_BASE_URL": "https://integrate.api.nvidia.com/v1",
    },
    "9router": {
        "NINEROUTER_KEY": "",
        "NINEROUTER_MODEL": "cx/gpt-5.2",
        "NINEROUTER_URL": "http://localhost:20128",
    },
    "ollama": {
        "OLLAMA_API_KEY": "",
        "OLLAMA_MODEL": "deepseek-v4-flash:cloud",
        "OLLAMA_HOST": "https://ollama.com",
    },
}

BASE_ENV_DEFAULTS = {
    "AI_COURT_LLM_PROVIDER": "auto",
    "AI_COURT_LLM_PRIMARY_PROVIDER": "openrouter",
    "AI_COURT_LLM_FALLBACK_PROVIDER": "groq",
    "AI_COURT_LLM_ENABLE_FALLBACK": "true",
}

VECTOR_SECTION = {
    "AI_COURT_VECTOR_API_URL": "",
    "AI_COURT_VECTOR_TIMEOUT_SECONDS": "30",
}


def masked(value: str) -> str:
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def load_current_env(env_path: Path) -> dict[str, str]:
    values = dotenv_values(env_path)
    return {key: value for key, value in values.items() if value is not None}


def save_env_values(env_path: Path, updates: dict[str, str]) -> None:
    env_path.parent.mkdir(parents=True, exist_ok=True)
    if not env_path.exists():
        env_path.write_text("", encoding="utf-8")

    for key, value in updates.items():
        set_key(str(env_path), key, value, quote_mode="never")


def prompt_choice(title: str, options: list[str], current: str | None = None) -> str:
    print(title)
    for index, option in enumerate(options, start=1):
        suffix = " (current)" if current == option else ""
        print(f"  {index}. {option}{suffix}")
    while True:
        raw = input("> ").strip()
        if raw.isdigit():
            choice = int(raw)
            if 1 <= choice <= len(options):
                return options[choice - 1]
        lowered = raw.lower()
        if lowered in options:
            return lowered
        print("Invalid choice. Please select a listed option.")


def prompt_text(label: str, current: str, *, secret: bool = False) -> str:
    display_current = masked(current) if secret else (current or "(empty)")
    print(f"{label} [{display_current}]")
    raw = getpass.getpass("> ") if secret else input("> ")
    value = raw.strip()
    return value or current


def configure_provider(env_path: Path, provider: str) -> None:
    current = load_current_env(env_path)
    updates: dict[str, str] = {}
    for key, default in CONFIG_SECTIONS[provider].items():
        existing = current.get(key, default)
        is_secret = key.endswith("_API_KEY") or key.endswith("_KEY")
        updates[key] = prompt_text(key, existing, secret=is_secret)

    updates["AI_COURT_LLM_PROVIDER"] = provider
    save_env_values(env_path, updates)
    print(f"Saved {provider} configuration to {env_path}.")


def configure_provider_mode(env_path: Path) -> None:
    current = load_current_env(env_path)
    selected = prompt_choice(
        "Select the active provider:",
        PROVIDER_OPTIONS,
        current.get("AI_COURT_LLM_PROVIDER", BASE_ENV_DEFAULTS["AI_COURT_LLM_PROVIDER"]),
    )
    save_env_values(env_path, {"AI_COURT_LLM_PROVIDER": selected})
    print(f"Active provider set to {selected}.")


def configure_fallback_chain(env_path: Path) -> None:
    current = load_current_env(env_path)
    primary = prompt_choice(
        "Select the primary provider for auto mode:",
        ["openrouter", "groq", "deepseek", "nvidia", "9router", "ollama"],
        current.get("AI_COURT_LLM_PRIMARY_PROVIDER", BASE_ENV_DEFAULTS["AI_COURT_LLM_PRIMARY_PROVIDER"]),
    )
    fallback = prompt_choice(
        "Select the fallback provider for auto mode:",
        ["openrouter", "groq", "deepseek", "nvidia", "9router", "ollama", "heuristic"],
        current.get("AI_COURT_LLM_FALLBACK_PROVIDER", BASE_ENV_DEFAULTS["AI_COURT_LLM_FALLBACK_PROVIDER"]),
    )
    enabled = prompt_choice(
        "Enable fallback retries?",
        ["true", "false"],
        current.get("AI_COURT_LLM_ENABLE_FALLBACK", BASE_ENV_DEFAULTS["AI_COURT_LLM_ENABLE_FALLBACK"]),
    )
    save_env_values(
        env_path,
        {
            "AI_COURT_LLM_PRIMARY_PROVIDER": primary,
            "AI_COURT_LLM_FALLBACK_PROVIDER": fallback,
            "AI_COURT_LLM_ENABLE_FALLBACK": enabled,
        },
    )
    print("Fallback chain updated.")


def print_summary(env_path: Path) -> None:
    current = {**BASE_ENV_DEFAULTS, **load_current_env(env_path)}
    print(f"\nConfig file: {env_path}")
    print(f"Active provider: {current['AI_COURT_LLM_PROVIDER']}")
    print(f"Auto primary: {current['AI_COURT_LLM_PRIMARY_PROVIDER']}")
    print(f"Auto fallback: {current['AI_COURT_LLM_FALLBACK_PROVIDER']}")
    print(f"Fallback enabled: {current['AI_COURT_LLM_ENABLE_FALLBACK']}")
    for provider, values in CONFIG_SECTIONS.items():
        print(f"\n[{provider}]")
        for key, default in values.items():
            value = current.get(key, default)
            if key.endswith("_API_KEY") or key.endswith("_KEY"):
                value = masked(value)
            print(f"  {key} = {value}")
    print("\n[vector]")
    for key, default in VECTOR_SECTION.items():
        value = current.get(key, default)
        print(f"  {key} = {value or '(empty)'}")
    print()


def ensure_defaults(env_path: Path) -> None:
    current = load_current_env(env_path)
    missing = {
        key: value for key, value in BASE_ENV_DEFAULTS.items() if key not in current
    }
    if missing:
        save_env_values(env_path, missing)


def configure_vector_lane(env_path: Path) -> None:
    current = load_current_env(env_path)
    updates: dict[str, str] = {}
    for key, default in VECTOR_SECTION.items():
        existing = current.get(key, default)
        updates[key] = prompt_text(key, existing, secret=False)
    save_env_values(env_path, updates)
    print("Remote vector lane configuration saved.")


def main() -> None:
    load_repo_env()
    env_path = get_repo_env_path()
    ensure_defaults(env_path)

    menu = [
        ("Set active provider", configure_provider_mode),
        ("Set auto fallback chain", configure_fallback_chain),
        ("Configure OpenRouter", lambda path: configure_provider(path, "openrouter")),
        ("Configure Groq", lambda path: configure_provider(path, "groq")),
        ("Configure DeepSeek", lambda path: configure_provider(path, "deepseek")),
        ("Configure NVIDIA NIM", lambda path: configure_provider(path, "nvidia")),
        ("Configure 9Router", lambda path: configure_provider(path, "9router")),
        ("Configure Ollama Cloud", lambda path: configure_provider(path, "ollama")),
        ("Configure Colab vector URL", configure_vector_lane),
        ("Show current config", print_summary),
        ("Exit", None),
    ]

    while True:
        print("\nAI Courtroom Harness Provider Config")
        for index, (label, _) in enumerate(menu, start=1):
            print(f"{index}. {label}")
        raw = input("> ").strip()
        if not raw.isdigit():
            print("Please enter a menu number.")
            continue

        choice = int(raw)
        if not 1 <= choice <= len(menu):
            print("Menu choice out of range.")
            continue

        label, action = menu[choice - 1]
        if action is None:
            print("Exiting provider config.")
            return

        print(f"\n{label}")
        action(env_path)


if __name__ == "__main__":
    main()
