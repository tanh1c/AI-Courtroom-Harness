from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

import httpx

from packages.shared.python.ai_court_shared.env_config import load_repo_env


load_repo_env()


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
        self.configured_provider = configured_provider
        self.timeout_seconds = float(os.getenv("AI_COURT_LLM_TIMEOUT_SECONDS", "60"))
        self.primary_provider = os.getenv("AI_COURT_LLM_PRIMARY_PROVIDER", "openrouter").strip().lower()
        self.fallback_provider = os.getenv("AI_COURT_LLM_FALLBACK_PROVIDER", "groq").strip().lower()
        self.enable_fallback = os.getenv("AI_COURT_LLM_ENABLE_FALLBACK", "true").strip().lower() not in {
            "0",
            "false",
            "no",
        }
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openrouter_base_url = os.getenv(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        ).rstrip("/")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "inclusionai/ring-2.6-1t:free").strip()
        self.http_referer = os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
        self.x_title = os.getenv("OPENROUTER_X_TITLE", "AI Courtroom Harness").strip()
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_base_url = os.getenv(
            "GROQ_BASE_URL",
            "https://api.groq.com/openai/v1",
        ).rstrip("/")
        self.groq_model = os.getenv("GROQ_MODEL", "qwen/qwen3-32b").strip()
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.deepseek_base_url = os.getenv(
            "DEEPSEEK_BASE_URL",
            "https://api.deepseek.com",
        ).rstrip("/")
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro").strip()
        self.deepseek_thinking = os.getenv("DEEPSEEK_THINKING", "disabled").strip().lower()
        self.deepseek_reasoning_effort = os.getenv("DEEPSEEK_REASONING_EFFORT", "high").strip().lower()
        self.deepseek_max_tokens = int(os.getenv("DEEPSEEK_MAX_TOKENS", "2048"))
        self.ninerouter_api_key = os.getenv("NINEROUTER_KEY", "").strip()
        self.ninerouter_base_url = os.getenv(
            "NINEROUTER_URL",
            "http://localhost:20128",
        ).rstrip("/")
        self.ninerouter_model = os.getenv("NINEROUTER_MODEL", "cx/gpt-5.2").strip()
        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY", "").strip()
        self.nvidia_base_url = os.getenv(
            "NVIDIA_BASE_URL",
            "https://integrate.api.nvidia.com/v1",
        ).rstrip("/")
        self.nvidia_model = os.getenv("NVIDIA_MODEL", "z-ai/glm4.7").strip()
        self.ollama_api_key = os.getenv("OLLAMA_API_KEY", "").strip()
        self.ollama_host = os.getenv("OLLAMA_HOST", "https://ollama.com").rstrip("/")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-v4-flash:cloud").strip()
        self._last_used_label: str | None = None
        if configured_provider == "auto":
            self.provider = "auto"
        else:
            self.provider = configured_provider

    def is_enabled(self) -> bool:
        return bool(self._provider_candidates())

    def provider_label(self) -> str:
        if self._last_used_label:
            return self._last_used_label
        if self.provider == "openrouter" and self._provider_available("openrouter"):
            return f"openrouter:{self.openrouter_model}"
        if self.provider == "groq" and self._provider_available("groq"):
            return f"groq:{self.groq_model}"
        if self.provider == "deepseek" and self._provider_available("deepseek"):
            return f"deepseek:{self.deepseek_model}"
        if self.provider == "9router" and self._provider_available("9router"):
            return f"9router:{self.ninerouter_model}"
        if self.provider == "nvidia" and self._provider_available("nvidia"):
            return f"nvidia:{self.nvidia_model}"
        if self.provider == "ollama" and self._provider_available("ollama"):
            return f"ollama:{self.ollama_model}"
        if self.provider == "auto":
            candidates = self._provider_candidates()
            if candidates:
                return self._provider_label(candidates[0])
        return "heuristic"

    def _provider_available(self, provider: str) -> bool:
        if provider == "openrouter":
            return bool(self.openrouter_api_key)
        if provider == "groq":
            return bool(self.groq_api_key)
        if provider == "deepseek":
            return bool(self.deepseek_api_key)
        if provider == "9router":
            return bool(self.ninerouter_api_key) and bool(self.ninerouter_base_url)
        if provider == "nvidia":
            return bool(self.nvidia_api_key)
        if provider == "ollama":
            return bool(self.ollama_api_key)
        return False

    def _provider_label(self, provider: str) -> str:
        if provider == "openrouter":
            return f"openrouter:{self.openrouter_model}"
        if provider == "groq":
            return f"groq:{self.groq_model}"
        if provider == "deepseek":
            return f"deepseek:{self.deepseek_model}"
        if provider == "9router":
            return f"9router:{self.ninerouter_model}"
        if provider == "nvidia":
            return f"nvidia:{self.nvidia_model}"
        if provider == "ollama":
            return f"ollama:{self.ollama_model}"
        return "heuristic"

    def _append_candidate(self, providers: list[str], provider: str) -> None:
        if provider in {"", "heuristic"}:
            return
        if provider in providers:
            return
        if self._provider_available(provider):
            providers.append(provider)

    def _provider_candidates(self) -> list[str]:
        providers: list[str] = []
        if self.provider == "auto":
            self._append_candidate(providers, self.primary_provider)
            if self.enable_fallback:
                self._append_candidate(providers, self.fallback_provider)
        elif self.provider == "heuristic":
            return []
        else:
            self._append_candidate(providers, self.provider)
            if self.enable_fallback and self.provider == self.primary_provider:
                self._append_candidate(providers, self.fallback_provider)
        return providers

    def _request_chat_completion(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        extra_headers: dict[str, str] | None = None,
        extra_payload: dict[str, Any] | None = None,
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
        if extra_payload:
            payload.update(extra_payload)

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return data

    def _generate_with_provider(
        self,
        provider: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        if provider == "openrouter":
            extra_headers: dict[str, str] = {}
            if self.http_referer:
                extra_headers["HTTP-Referer"] = self.http_referer
            if self.x_title:
                extra_headers["X-Title"] = self.x_title
            return self._request_chat_completion(
                base_url=self.openrouter_base_url,
                api_key=self.openrouter_api_key,
                model=self.openrouter_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                extra_headers=extra_headers,
            )
        if provider == "groq":
            return self._request_chat_completion(
                base_url=self.groq_base_url,
                api_key=self.groq_api_key,
                model=self.groq_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        if provider == "deepseek":
            extra_payload: dict[str, Any] = {
                "response_format": {"type": "json_object"},
                "max_tokens": max_tokens or self.deepseek_max_tokens,
            }
            if self.deepseek_thinking in {"enabled", "disabled"}:
                extra_payload["thinking"] = {"type": self.deepseek_thinking}
            if self.deepseek_thinking == "enabled" and self.deepseek_reasoning_effort in {"high", "max"}:
                extra_payload["reasoning_effort"] = self.deepseek_reasoning_effort
            return self._request_chat_completion(
                base_url=self.deepseek_base_url,
                api_key=self.deepseek_api_key,
                model=self.deepseek_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                extra_payload=extra_payload,
            )
        if provider == "9router":
            return self._request_chat_completion(
                base_url=f"{self.ninerouter_base_url}/v1",
                api_key=self.ninerouter_api_key,
                model=self.ninerouter_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        if provider == "nvidia":
            from openai import OpenAI

            client = OpenAI(
                base_url=self.nvidia_base_url,
                api_key=self.nvidia_api_key,
            )
            completion = client.chat.completions.create(
                model=self.nvidia_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                top_p=1,
                max_tokens=4096,
                extra_body={
                    "chat_template_kwargs": {
                        "enable_thinking": True,
                        "clear_thinking": False,
                    }
                },
            )
            return completion.model_dump()
        if provider == "ollama":
            from ollama import Client

            client = Client(
                host=self.ollama_host,
                headers={"Authorization": f"Bearer {self.ollama_api_key}"},
            )
            return client.chat(
                model=self.ollama_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        raise RuntimeError(f"Unsupported LLM provider: {provider}")

    def generate_json(self, system_prompt: str, user_prompt: str, *, max_tokens: int | None = None) -> dict:
        self._last_used_label = None
        candidates = self._provider_candidates()
        if not candidates:
            raise RuntimeError("No LLM provider is enabled.")

        last_error: Exception | None = None
        for provider in candidates:
            try:
                data = self._generate_with_provider(provider, system_prompt, user_prompt, max_tokens=max_tokens)
                if provider == "ollama":
                    content = data["message"]["content"]
                else:
                    content = data["choices"][0]["message"]["content"]
                if isinstance(content, list):
                    joined = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            joined.append(item.get("text", ""))
                    content = "\n".join(joined)
                if not isinstance(content, str):
                    raise ValueError("Unexpected provider response format.")
                payload = _extract_json_object(content)
                self._last_used_label = self._provider_label(provider)
                return payload
            except Exception as error:
                last_error = error
                continue

        if last_error is not None:
            raise last_error
        raise RuntimeError("No provider succeeded.")


@lru_cache(maxsize=1)
def get_courtroom_llm_service() -> CourtroomLlmService:
    return CourtroomLlmService()
