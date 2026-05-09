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

    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[index:])
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            continue
    raise ValueError("Model response did not contain a valid JSON object.")


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
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_base_url = os.getenv(
            "GROQ_BASE_URL",
            "https://api.groq.com/openai/v1",
        ).rstrip("/")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
        if configured_provider == "auto":
            if self.openrouter_api_key:
                self.provider = "openrouter"
            elif self.groq_api_key:
                self.provider = "groq"
            else:
                self.provider = "heuristic"
        else:
            self.provider = configured_provider

    def is_enabled(self) -> bool:
        if self.provider == "openrouter":
            return bool(self.openrouter_api_key)
        if self.provider == "groq":
            return bool(self.groq_api_key)
        return False

    def provider_label(self) -> str:
        if self.provider == "openrouter" and self.is_enabled():
            return f"openrouter:{self.openrouter_model}"
        if self.provider == "groq" and self.is_enabled():
            return f"groq:{self.groq_model}"
        return "heuristic"

    def _request_chat_completion(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        extra_headers: dict[str, str] | None = None,
    ) -> dict:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        payload = {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return data

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.is_enabled():
            raise RuntimeError("No LLM provider is enabled.")

        if self.provider == "openrouter":
            extra_headers: dict[str, str] = {}
            if self.http_referer:
                extra_headers["HTTP-Referer"] = self.http_referer
            if self.x_title:
                extra_headers["X-Title"] = self.x_title
            data = self._request_chat_completion(
                base_url=self.openrouter_base_url,
                api_key=self.openrouter_api_key,
                model=self.openrouter_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                extra_headers=extra_headers,
            )
        elif self.provider == "groq":
            data = self._request_chat_completion(
                base_url=self.groq_base_url,
                api_key=self.groq_api_key,
                model=self.groq_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        else:
            raise RuntimeError(f"Unsupported LLM provider: {self.provider}")

        content = data["choices"][0]["message"]["content"]
        if isinstance(content, list):
            joined = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    joined.append(item.get("text", ""))
            content = "\n".join(joined)
        if not isinstance(content, str):
            raise ValueError("Unexpected provider response format.")
        return _extract_json_object(content)


@lru_cache(maxsize=1)
def get_courtroom_llm_service() -> CourtroomLlmService:
    return CourtroomLlmService()
