"""LLM access layer.

Supports any OpenAI-compatible chat completions endpoint (DeepSeek, OpenAI,
Moonshot, Qwen, SiliconFlow, ...) and Anthropic's Messages API.  The rest of
the application only talks to :class:`LLMClient`.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from ..config import get_settings


class LLMError(RuntimeError):
    """Raised when the upstream model cannot be reached or returns garbage."""


class LLMNotConfigured(LLMError):
    pass


@dataclass
class LLMResult:
    text: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def extract_json(text: str) -> Any:
    """Best-effort JSON extraction from an LLM answer."""
    if not text:
        raise LLMError("empty model response")
    candidate = text.strip()
    fenced = _JSON_BLOCK.search(candidate)
    if fenced:
        candidate = fenced.group(1).strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    # Fall back to the outermost object/array in the text.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = candidate.find(opener)
        end = candidate.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise LLMError("model did not return valid JSON")


class LLMClient:
    def __init__(
        self,
        *,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        settings = get_settings()
        self.provider = (provider or settings.LLM_PROVIDER).lower()
        self.api_key = api_key if api_key is not None else settings.LLM_API_KEY
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE if temperature is None else temperature
        self.timeout = timeout or settings.LLM_TIMEOUT_SECONDS
        self.max_retries = settings.LLM_MAX_RETRIES if max_retries is None else max_retries

    # ------------------------------------------------------------------
    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        json_mode: bool = False,
    ) -> LLMResult:
        if not self.configured:
            raise LLMNotConfigured(
                "LLM_API_KEY is not set - configure it in .env before generating papers"
            )
        settings = get_settings()
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        temperature = self.temperature if temperature is None else temperature
        model = model or self.model

        last_error: Optional[Exception] = None
        for attempt in range(1, max(1, self.max_retries) + 1):
            try:
                if self.provider == "anthropic":
                    return await self._complete_anthropic(
                        messages, model, max_tokens, temperature
                    )
                return await self._complete_openai(
                    messages, model, max_tokens, temperature, json_mode
                )
            except (httpx.TimeoutException, httpx.TransportError, LLMError) as exc:
                last_error = exc
                if isinstance(exc, LLMNotConfigured):
                    raise
                if attempt >= self.max_retries:
                    break
                await asyncio.sleep(min(2 ** attempt, 8))
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code
                # 4xx other than rate limiting will not get better by retrying.
                if status not in (408, 409, 429, 500, 502, 503, 504):
                    detail = exc.response.text[:300]
                    raise LLMError(
                        f"upstream model rejected the request ({status}): {detail}"
                    ) from exc
                if attempt >= self.max_retries:
                    break
                retry_after = exc.response.headers.get("retry-after")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 10)
                await asyncio.sleep(delay)
        raise LLMError(f"model request failed after {self.max_retries} attempts: {last_error}")

    # ------------------------------------------------------------------
    async def _complete_openai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool,
    ) -> LLMResult:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
        try:
            choice = data["choices"][0]
            text = (choice.get("message") or {}).get("content") or ""
        except (KeyError, IndexError) as exc:
            raise LLMError(f"unexpected model response: {str(data)[:300]}") from exc
        usage = data.get("usage") or {}
        return LLMResult(
            text=text.strip(),
            model=data.get("model", model),
            tokens_in=int(usage.get("prompt_tokens") or 0),
            tokens_out=int(usage.get("completion_tokens") or 0),
        )

    async def _complete_anthropic(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResult:
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        turns = [m for m in messages if m["role"] != "system"]
        payload: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": turns,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        base = self.base_url
        if "anthropic.com" not in base:
            base = "https://api.anthropic.com"
        headers = {
            "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{base}/v1/messages", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        text = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        )
        usage = data.get("usage") or {}
        return LLMResult(
            text=text.strip(),
            model=data.get("model", model),
            tokens_in=int(usage.get("input_tokens") or 0),
            tokens_out=int(usage.get("output_tokens") or 0),
        )

    async def complete_json(
        self,
        messages: List[Dict[str, str]],
        *,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
    ) -> tuple[Any, LLMResult]:
        result = await self.complete(
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
            json_mode=True,
        )
        try:
            return extract_json(result.text), result
        except LLMError:
            # One repair attempt: ask the model to resend strictly valid JSON.
            repair = list(messages) + [
                {"role": "assistant", "content": result.text[:4000]},
                {
                    "role": "user",
                    "content": "Your previous answer was not valid JSON. Reply with ONLY the JSON object, no prose, no code fences.",
                },
            ]
            second = await self.complete(
                repair, max_tokens=max_tokens, temperature=0.0, model=model, json_mode=True
            )
            return extract_json(second.text), second

    async def ping(self) -> str:
        result = await self.complete(
            [{"role": "user", "content": "Reply with exactly: ok"}], max_tokens=8, temperature=0
        )
        return result.text


_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
