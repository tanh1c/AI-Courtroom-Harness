from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.orchestration.python.ai_court_orchestration.llm import (
    get_courtroom_llm_service,
)


def main() -> None:
    service = get_courtroom_llm_service()
    if not service.is_enabled():
        raise SystemExit(
            "No provider is enabled. Set OPENROUTER_API_KEY or GROQ_API_KEY, or explicitly set AI_COURT_LLM_PROVIDER."
        )

    payload = service.generate_json(
        system_prompt=(
            "Return strict JSON only with shape "
            "{\"message\": string, \"model_hint\": string}. "
            "Write concise Vietnamese."
        ),
        user_prompt=(
            "Write a one-sentence courtroom simulation greeting and include the configured model name "
            "in model_hint."
        ),
    )
    print("provider:", service.provider_label())
    if service.provider == "openrouter":
        print("configured_model:", os.getenv("OPENROUTER_MODEL", "openrouter/free"))
    elif service.provider == "groq":
        print("configured_model:", os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"))
    print("message:", payload.get("message"))
    print("model_hint:", payload.get("model_hint"))


if __name__ == "__main__":
    main()
