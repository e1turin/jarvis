"""
Pure LLM client — wraps OpenAI-compatible API calls.
Single responsibility: send messages, get responses.
No tool logic, no conversation history, no orchestration.
"""

from __future__ import annotations

from typing import Any

from openai import OpenAI, APIError, APITimeoutError, APIConnectionError
from jarvis.config import settings


class LLMError(Exception):
    """Base exception for LLM client errors."""


class LLMConnectionError(LLMError):
    """Could not connect to the LLM server."""


class LLMTimeoutError(LLMError):
    """LLM request timed out."""


class LLMAPIError(LLMError):
    """LLM API returned an error."""


class LLMClient:
    """
    Minimal LLM client. Takes messages, returns responses.
    No tools, no history, no orchestration — just the API call.
    """

    def __init__(self):
        # Proxy is auto-detected from HTTP_PROXY / HTTPS_PROXY / NO_PROXY
        # environment variables (loaded from .env by python-dotenv).
        self.client = OpenAI(
            base_url=settings.llm_base_url or None,
            api_key=settings.llm_api_key,
            timeout=settings.llm_timeout,
            max_retries=settings.llm_max_retries,
        )
        self.model = settings.llm_model

    def send(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
    ) -> Any:
        """
        Send messages to the LLM and return the raw response.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of OpenAI tool definitions.

        Returns:
            OpenAI chat completion response object.

        Raises:
            LLMConnectionError: Server unreachable.
            LLMTimeoutError: Request timed out.
            LLMAPIError: API returned an error.
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        try:
            return self.client.chat.completions.create(**kwargs)
        except APIConnectionError as e:
            raise LLMConnectionError(
                "Could not connect to the LLM server. "
                "Is LM Studio running and the server started?"
            ) from e
        except APITimeoutError as e:
            raise LLMTimeoutError(
                "LLM request timed out. The model may still be loading."
            ) from e
        except APIError as e:
            # Wrap for retry detection (status_code is useful)
            raise LLMAPIError(str(e)) from e

    @property
    def provider_label(self) -> str:
        """Return a short human-readable provider name."""
        url = settings.llm_base_url.lower()
        if "localhost:1234" in url or "127.0.0.1:1234" in url:
            return "LM Studio"
        elif "localhost:11434" in url or "127.0.0.1:11434" in url:
            return "Ollama"
        elif "openai" in url:
            return "OpenAI"
        else:
            return url
