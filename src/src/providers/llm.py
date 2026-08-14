"""LLM provider seam: LiteLLM (real) ↔ deterministic Stub."""

from __future__ import annotations

import json
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from ..core.logging import get_logger

log = get_logger(__name__)

Message = Dict[str, str]  # {"role": "user|assistant|system", "content": "..."}


class LLMProvider(ABC):
    name = "base"
    is_stub = False

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        *,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        ...

    @abstractmethod
    def stream(
        self,
        messages: List[Message],
        *,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        ...

    async def json_complete(
        self,
        messages: List[Message],
        *,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Default: complete then parse JSON (robust to ```json fences)."""
        raw = await self.complete(messages, system=system, temperature=temperature, max_tokens=max_tokens)
        return _safe_json(raw)


def _safe_json(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, dict):
            return parsed
    except Exception:  # noqa: BLE001
        pass
    return {}


class StubLLM(LLMProvider):
    """Deterministic, dependency-free responder mirroring mock.ts respond()."""

    name = "stub"
    is_stub = True

    async def complete(
        self,
        messages: List[Message],
        *,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        from ..domain.skills.routing import canned_reply

        last = messages[-1]["content"] if messages else ""
        return canned_reply(last)

    async def stream(
        self,
        messages: List[Message],
        *,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        from ..domain.skills.routing import canned_reply

        last = messages[-1]["content"] if messages else ""
        text = canned_reply(last)
        # Token-ish streaming for the typewriter effect.
        for tok in _tokenize(text):
            yield tok


def _tokenize(text: str):
    import re

    for part in re.findall(r"[\s]+|[^\s]+", text):
        yield part


class LiteLLMProvider(LLMProvider):
    """Real LLM via LiteLLM (OpenAI-compatible, Azure, Anthropic, …)."""

    name = "litellm"

    def __init__(self, model: str, api_key: Optional[str], api_base: Optional[str]) -> None:
        try:
            import litellm  # type: ignore  # noqa: F401
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("litellm is not installed (pip install -e .[llm])") from exc
        self.model = model
        self.api_key = api_key
        self.api_base = api_base

    def _payload(
        self, messages: List[Message], system: Optional[str], temperature: float, max_tokens: int, stream: bool
    ):
        msgs: List[Message] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base
        return kwargs

    async def complete(
        self,
        messages: List[Message],
        *,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        import litellm  # type: ignore

        resp = await litellm.acompletion(
            **self._payload(messages, system, temperature, max_tokens, stream=False)
        )
        return resp["choices"][0]["message"]["content"] or ""

    async def stream(
        self,
        messages: List[Message],
        *,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        import litellm  # type: ignore

        resp = await litellm.acompletion(
            **self._payload(messages, system, temperature, max_tokens, stream=True)
        )
        async for chunk in resp:  # type: ignore[union-attr]
            try:
                delta = chunk["choices"][0]["delta"].get("content")
            except (KeyError, IndexError):  # noqa: BLE001
                delta = None
            if delta:
                yield delta


class DeepTutorProvider(LLMProvider):
    """LLM seam backed by DeepTutor's unified agent WebSocket API.

    DeepTutor is an agent service, not an OpenAI-compatible model endpoint.
    Each PLOS turn is therefore submitted as a ``message`` turn and this
    adapter relays its answer-visible ``content`` events to the caller.
    """

    name = "deeptutor"

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        capability: str = "chat",
        language: str = "zh",
    ) -> None:
        self.ws_url = self._websocket_url(base_url)
        self.token = token
        self.capability = capability
        self.language = language

    @staticmethod
    def _websocket_url(base_url: str) -> str:
        parsed = urlparse(base_url.strip())
        if parsed.scheme not in {"http", "https", "ws", "wss"} or not parsed.netloc:
            raise ValueError("PLOS_DEEPTUTOR_BASE_URL must be an absolute HTTP(S) or WS(S) URL")
        scheme = {"http": "ws", "https": "wss"}.get(parsed.scheme, parsed.scheme)
        path = parsed.path.rstrip("/")
        if not path.endswith("/api/v1/ws"):
            path = f"{path}/api/v1/ws" if path else "/api/v1/ws"
        return urlunparse((scheme, parsed.netloc, path, "", "", ""))

    @property
    def _connect_url(self) -> str:
        """DeepTutor reads WS credentials from the ``token`` query parameter."""
        if not self.token:
            return self.ws_url
        parsed = urlparse(self.ws_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["token"] = self.token
        return urlunparse(parsed._replace(query=urlencode(query)))

    def _turn_payload(self, messages: List[Message], system: Optional[str]) -> Dict[str, Any]:
        # PLOS passes the complete thread. DeepTutor's wire contract has a
        # single content field, so retain preceding turns as explicit context.
        prior = messages[:-1]
        last = messages[-1]["content"] if messages else ""
        context: List[str] = []
        if system:
            context.append(f"[System instruction]\n{system}")
        for message in prior:
            role = message.get("role", "user")
            content = message.get("content", "")
            if content:
                context.append(f"[{role}]\n{content}")
        content = "\n\n".join([*context, f"[User]\n{last}"])
        return {
            "type": "message",
            "content": content,
            "capability": self.capability,
            "language": self.language,
        }

    async def complete(
        self,
        messages: List[Message],
        *,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        return "".join([chunk async for chunk in self.stream(messages, system=system, temperature=temperature, max_tokens=max_tokens)])

    async def stream(
        self,
        messages: List[Message],
        *,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        try:
            import websockets  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("websockets is required for the DeepTutor provider") from exc

        try:
            async with websockets.connect(self._connect_url) as socket:
                await socket.send(json.dumps(self._turn_payload(messages, system), ensure_ascii=False))
                while True:
                    event = json.loads(await socket.recv())
                    kind = event.get("type")
                    if kind == "content":
                        content = event.get("content")
                        if content:
                            yield str(content)
                    elif kind == "error":
                        raise RuntimeError(f"DeepTutor turn failed: {event.get('content') or event.get('message') or 'unknown error'}")
                    elif kind == "done":
                        return
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"DeepTutor service unavailable at {self.ws_url}: {exc}") from exc
