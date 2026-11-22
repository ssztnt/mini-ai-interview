"""A thin, provider-agnostic wrapper around the OpenAI SDK.

Both OpenAI and Microsoft Foundry expose the same OpenAI v1 API, so one client
covers both. Every call asks for **structured output**: the response must match
a Pydantic schema, which the SDK turns into a strict JSON schema.
"""

import logging
from typing import Protocol, TypeVar

import openai
from pydantic import BaseModel, ValidationError

from app.config import LLMConfig

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """The LLM call failed or returned something unusable."""


class LLMClient(Protocol):
    def generate(self, *, system: str, user: str, schema: type[T]) -> T:
        """Send a system + user prompt and return a validated `schema` instance."""
        ...


class OpenAIClient:
    def __init__(self, config: LLMConfig, *, max_attempts: int = 2) -> None:
        self._model = config.model
        self._max_attempts = max_attempts
        self._client = openai.OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=60,
            max_retries=2,  # SDK-level retries for network errors / 429 / 5xx
        )

    def generate(self, *, system: str, user: str, schema: type[T]) -> T:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        last_error: Exception | None = None

        # Our own retry loop handles malformed or truncated structured output,
        # which the SDK does not retry on its own.
        for attempt in range(1, self._max_attempts + 1):
            try:
                completion = self._client.chat.completions.parse(
                    model=self._model,
                    messages=messages,
                    response_format=schema,
                )
                message = completion.choices[0].message
                if message.refusal:
                    raise LLMError(f"Model refused the request: {message.refusal}")
                if message.parsed is None:
                    raise LLMError("Model returned no structured output")
                return message.parsed
            except (ValidationError, openai.LengthFinishReasonError) as exc:
                last_error = exc
                logger.warning("Structured output invalid (attempt %d): %s", attempt, exc)
            except openai.AuthenticationError as exc:
                raise LLMError("The LLM provider rejected the API key") from exc
            except openai.APIError as exc:
                raise LLMError(f"LLM provider error: {exc}") from exc

        raise LLMError("Model did not return valid structured output") from last_error
