from __future__ import annotations

import json
import os
from functools import lru_cache

import httpx


def _extract_json_object(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model response did not contain a JSON object.")
    return json.loads(text[start : end + 1])


class CourtroomLlmService:
    def __init__(self) -> None:
        configured_provider = os.getenv("AI_COURT_LLM_PROVIDER", "auto").strip().lower()
        self.timeout_seconds = float(os.getenv("AI_COURT_LLM_TIMEOUT_SECONDS", "60"))
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openrouter_base_url = os.getenv(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        ).rstrip("/")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()
        self.http_referer = os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
        self.x_title = os.getenv("OPENROUTER_X_TITLE", "AI Courtroom Harness").strip()
        if configured_provider == "auto":
            self.provider = "openrouter" if self.openrouter_api_key else "heuristic"
        else:
            self.provider = configured_provider

    def is_enabled(self) -> bool:
        return self.provider == "openrouter" and bool(self.openrouter_api_key)

    def provider_label(self) -> str:
        if self.is_enabled():
            return f"openrouter:{self.openrouter_model}"
        return "heuristic"

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.is_enabled():
            raise RuntimeError("OpenRouter provider is not enabled.")

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.x_title:
            headers["X-Title"] = self.x_title

        payload = {
            "model": self.openrouter_model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        if isinstance(content, list):
            joined = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    joined.append(item.get("text", ""))
            content = "\n".join(joined)
        if not isinstance(content, str):
            raise ValueError("Unexpected OpenRouter response format.")
        return _extract_json_object(content)


@lru_cache(maxsize=1)
def get_courtroom_llm_service() -> CourtroomLlmService:
    return CourtroomLlmService()
