"""OpenAI-compatible backend: DeepSeek, Kimi, ChatGPT, or any provider that speaks /chat/completions.

Added 2026-10-04 so a role can be given a model outside the two measured engines. It follows the
test-only client of the July A/B (src/p3map/ab/ab_deepseek.py), which is the one shape that worked
there: `response_format: json_object`, with the JSON Schema appended to the user turn, because a
forced tool call is refused by more than one of these providers' reasoning models. The system
prefix is sent untouched, so a provider that caches prompt prefixes can cache it.

What differs between providers is declared, not coded: config/llm/engines.json gives each engine
its `base_url`, the variable its key is read from, and a `request` block (which field limits the
reply, whether a temperature is sent, extra fields such as a thinking switch), with a model's own
block laid over the engine's. Fixing a provider's quirk is an edit to that file.

NOT MEASURED. The prompts, the traps and every reported figure were made on Claude. This client
has been exercised against a local OpenAI-compatible server only; no judged row came from it.

The key is read from the environment when a call is made and is never stored on the object,
printed, or left in an error message. httpx only: the `openai` package is not a dependency.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field

import httpx

from config.llm.base import LLMClient, Usage

_RETRY_STATUS = {408, 409, 429, 500, 502, 503, 504, 529}
_BACKOFF = (2.0, 6.0, 15.0)
SCHEMA_INSTRUCTION = ("\n\nReturn ONLY a JSON object conforming to this JSON Schema "
                      "(no prose, no markdown fence):\n")


class ProviderError(RuntimeError):
    """The provider refused the request or answered with something that is not the JSON asked for."""


def parse_json(content: str) -> dict:
    """The object in a reply: the reply itself, or the outermost braces when it came wrapped."""
    try:
        doc = json.loads(content)
    except (TypeError, ValueError):
        m = re.search(r"\{.*\}", content or "", re.DOTALL)
        if not m:
            raise ProviderError("the reply holds no JSON object") from None
        try:
            doc = json.loads(m.group(0))
        except ValueError:
            raise ProviderError("the reply's JSON does not parse") from None
    if not isinstance(doc, dict):
        raise ProviderError("the reply is JSON but not an object")
    return doc


def read_usage(u: dict | None) -> Usage:
    """One call's tokens in the stage's own terms: input excludes what was read from the cache.

    The three providers name the cached part differently: DeepSeek `prompt_cache_hit_tokens`
    (with the miss beside it), OpenAI `prompt_tokens_details.cached_tokens`, Kimi `cached_tokens`.
    """
    u = u or {}
    details = u.get("prompt_tokens_details") or {}
    prompt = int(u.get("prompt_tokens") or 0)
    hit = int(u.get("prompt_cache_hit_tokens") or details.get("prompt_cache_hit_tokens")
              or details.get("cached_tokens") or u.get("cached_tokens") or 0)
    miss = u.get("prompt_cache_miss_tokens", details.get("prompt_cache_miss_tokens"))
    miss = int(miss) if miss is not None else max(prompt - hit, 0)
    return Usage(input_tokens=miss, output_tokens=int(u.get("completion_tokens") or 0),
                 cache_read_tokens=hit, calls=1)


@dataclass
class OpenAICompatClient(LLMClient):
    base_url: str = ""
    key_env: str = ""
    request: dict = field(default_factory=dict)
    timeout: float = 300.0

    def _body(self, prompt: str, schema: dict, system: str | None, max_tokens: int) -> dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt + SCHEMA_INSTRUCTION + json.dumps(schema)})
        body: dict = {"model": self.model, "messages": messages,
                      "response_format": {"type": "json_object"}}
        limit = max_tokens + int(self.request.get("max_tokens_extra") or 0)
        body[self.request.get("token_param") or "max_tokens"] = limit
        if self.request.get("temperature") is not None:
            body["temperature"] = self.request["temperature"]
        body.update(self.request.get("extra") or {})
        return body

    def complete(self, prompt: str, schema: dict, *, system: str | None = None,
                 max_tokens: int = 2048, cache_system: bool = False) -> dict:
        key = os.environ.get(self.key_env, "").strip() if self.key_env else ""
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        url = self.base_url.rstrip("/") + "/chat/completions"
        body = self._body(prompt, schema, system, max_tokens)

        def clean(text: str) -> str:
            return text.replace(key, "[key]") if key else text

        last = ""
        for attempt in range(len(_BACKOFF) + 1):
            try:
                r = httpx.post(url, json=body, headers=headers, timeout=self.timeout)
            except httpx.HTTPError as e:                       # no answer at all: worth another try
                last = f"{type(e).__name__}: {clean(str(e))[:160]}"
            else:
                if r.status_code == 200:
                    data = r.json()
                    self.usage.add(read_usage(data.get("usage")))
                    choice = (data.get("choices") or [{}])[0]
                    content = (choice.get("message") or {}).get("content") or ""
                    if not content.strip() and choice.get("finish_reason") == "length":
                        raise ProviderError(
                            f"{self.model} used its whole reply budget before answering; raise "
                            f"max_tokens_extra for it in engines.json")
                    return parse_json(content)
                last = f"HTTP {r.status_code}: {clean(r.text)[:200]}"
                if r.status_code not in _RETRY_STATUS:
                    break
            if attempt < len(_BACKOFF):
                time.sleep(_BACKOFF[attempt])
        raise ProviderError(f"{self.model} at {url}: {last}")
