"""OpenAI-compatible LLM client with response caching and call logging."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from .io import append_jsonl


class LLMError(RuntimeError):
    """The LLM request failed."""


class LLMValidationError(LLMError):
    """The endpoint returned text, but the caller's output validator rejected it."""

    def __init__(self, message: str, rejected_text: str | None = None) -> None:
        super().__init__(message)
        self.rejected_text = rejected_text


@dataclass
class LLMResponse:
    """Text and accounting for one LLM response."""
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    seconds: float
    cached: bool

    def to_dict(self) -> dict:
        return asdict(self)


class SQLiteCache:
    """Persistent key-value cache of LLM responses."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS responses (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        self._db.commit()

    def get(self, key: str):
        with self._lock:
            row = self._db.execute("SELECT value FROM responses WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, key: str, value: dict) -> None:
        payload = json.dumps(value, sort_keys=True)
        with self._lock:
            self._db.execute("INSERT OR REPLACE INTO responses(key, value) VALUES (?, ?)", (key, payload))
            self._db.commit()


class LLMClient:
    """Cached, retrying client for an OpenAI-compatible chat-completions endpoint."""
    def __init__(
        self,
        model: str,
        *,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        temperature: float = 0.0,
        max_retries: int = 2,
        cache_path: str | Path = "cache/llm_cache.sqlite",
        call_log: str | Path | None = None,
        transport: Callable[[str, str, float], tuple[str, int, int]] | None = None,
    ):
        if not model:
            raise ValueError("A model identifier is required")
        self.model = model
        self.api_key_env = api_key_env
        self.base_url = base_url
        self.temperature = float(temperature)
        self.max_retries = int(max_retries)
        self.cache = SQLiteCache(cache_path)
        self.call_log = Path(call_log) if call_log else None
        self.transport = transport
        self._client = None
        self._lock = threading.Lock()

    def _ensure_client(self):
        if self._client is not None or self.transport is not None:
            return
        from openai import OpenAI

        key = os.environ.get(self.api_key_env)
        if not key and not self.base_url:
            raise LLMError(f"Environment variable {self.api_key_env} is not set")
        with self._lock:
            if self._client is None:
                self._client = OpenAI(api_key=key or "EMPTY", base_url=self.base_url)

    def _request(self, prompt: str, system: str | None) -> tuple[str, int, int]:
        if self.transport is not None:
            return self.transport(prompt, self.model, self.temperature)
        self._ensure_client()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        assert self._client is not None
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        usage = getattr(response, "usage", None)
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        return response.choices[0].message.content or "", prompt_tokens, completion_tokens

    def complete(
        self,
        prompt: str,
        *,
        purpose: str,
        system: str | None = None,
        tag: str = "",
        meta: dict | None = None,
        validate: Callable[[str], object] | None = None,
        retry_on_validation_error: bool = True,
    ) -> LLMResponse:
        key_material = [self.model, self.base_url, self.temperature, system, tag, prompt]
        key = hashlib.sha256(json.dumps(key_material, sort_keys=True).encode("utf-8")).hexdigest()
        cached = self.cache.get(key)
        if cached is not None:
            try:
                if not isinstance(cached.get("text"), str) or not cached["text"].strip():
                    raise ValueError("Empty cached response")
                if validate:
                    validate(cached["text"])
            except Exception:
                cached = None
        if cached is not None:
            result = LLMResponse(
                text=cached["text"],
                model=self.model,
                prompt_tokens=int(cached.get("prompt_tokens", 0)),
                completion_tokens=int(cached.get("completion_tokens", 0)),
                seconds=0.0,
                cached=True,
            )
        else:
            last_error = None
            for attempt in range(self.max_retries + 1):
                started = time.perf_counter()
                try:
                    text, prompt_tokens, completion_tokens = self._request(prompt, system)
                except Exception as exc:
                    last_error = exc
                    if attempt < self.max_retries:
                        time.sleep(2 * (attempt + 1))
                        continue
                    raise LLMError(f"{purpose}: {type(exc).__name__}: {exc}") from exc

                validation_exc: Exception | None
                if not isinstance(text, str) or not text.strip():
                    validation_exc = ValueError("The LLM returned an empty response")
                else:
                    validation_exc = None
                    if validate:
                        try:
                            validate(text)
                        except Exception as exc:
                            validation_exc = exc

                if validation_exc is not None:
                    last_error = validation_exc
                    if not retry_on_validation_error:
                        raise LLMValidationError(
                            f"{purpose}: {type(validation_exc).__name__}: {validation_exc}",
                            rejected_text=text,
                        ) from validation_exc
                    if attempt < self.max_retries:
                        time.sleep(2 * (attempt + 1))
                        continue
                    raise LLMValidationError(
                        f"{purpose}: {type(validation_exc).__name__}: {validation_exc}"
                    ) from validation_exc

                result = LLMResponse(
                    text=text,
                    model=self.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    seconds=time.perf_counter() - started,
                    cached=False,
                )
                self.cache.put(
                    key,
                    {
                        "text": text,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                    },
                )
                break
            else:
                raise LLMError(f"{purpose}: {type(last_error).__name__}: {last_error}") from last_error

        if self.call_log:
            record = {
                "purpose": purpose,
                "model": result.model,
                "cached": result.cached,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "seconds": round(result.seconds, 6),
                "cache_key": key[:16],
            }
            record.update(meta or {})
            with self._lock:
                append_jsonl(self.call_log, record)
        return result


def client_from_config(cfg: dict, section: str, *, call_log: str | Path | None = None, transport: Callable[[str, str, float], tuple[str, int, int]] | None = None) -> LLMClient:
    """Build an ``LLMClient`` from the ``llm`` or ``judge`` configuration section."""
    settings = cfg[section]
    model = os.environ.get(settings["model_env"])
    if not model:
        raise LLMError(f"Environment variable {settings['model_env']} is not set")
    base_url = os.environ.get(settings.get("base_url_env", "")) or None
    cache_path = Path(cfg["_root"]) / cfg["llm"].get("cache_path", "cache/llm_cache.sqlite")
    return LLMClient(
        model=model,
        api_key_env=settings.get("api_key_env", "OPENAI_API_KEY"),
        base_url=base_url,
        temperature=float(settings.get("temperature", 0.0)),
        max_retries=int(settings.get("max_retries", 2)),
        cache_path=cache_path,
        call_log=call_log,
        transport=transport,
    )
