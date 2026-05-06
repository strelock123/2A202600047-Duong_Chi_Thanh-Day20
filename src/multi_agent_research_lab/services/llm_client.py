"""LLM client abstraction — OpenAI-backed with retry and cost tracking."""

import logging
import time
from dataclasses import dataclass

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError

logger = logging.getLogger(__name__)

# gpt-4o-mini pricing per 1K tokens (as of 2024)
_INPUT_COST_PER_1K = 0.00015
_OUTPUT_COST_PER_1K = 0.0006


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """OpenAI-backed LLM client with retry/backoff and token cost tracking."""

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.2,
        max_retries: int = 3,
    ) -> None:
        from openai import OpenAI

        settings = get_settings()
        self._client = OpenAI(api_key=settings.openai_api_key, timeout=60)
        self._model = model or settings.openai_model
        self._temperature = temperature
        self._max_retries = max_retries

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion with exponential-backoff retry."""
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = self._client.chat.completions.create(
                    model=self._model,
                    temperature=self._temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = resp.choices[0].message.content or ""
                usage = resp.usage
                in_tok = usage.prompt_tokens if usage else None
                out_tok = usage.completion_tokens if usage else None
                cost: float | None = None
                if in_tok and out_tok:
                    cost = (in_tok / 1000 * _INPUT_COST_PER_1K) + (out_tok / 1000 * _OUTPUT_COST_PER_1K)
                logger.debug(
                    "LLM ok: model=%s in=%s out=%s cost=%.5f",
                    self._model,
                    in_tok,
                    out_tok,
                    cost or 0,
                )
                return LLMResponse(
                    content=content,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    cost_usd=cost,
                )
            except Exception as exc:
                last_exc = exc
                logger.warning("LLM attempt %d/%d failed: %s", attempt + 1, self._max_retries, exc)
                if attempt < self._max_retries - 1:
                    time.sleep(2**attempt)
        raise AgentExecutionError(
            f"LLM failed after {self._max_retries} retries: {last_exc}"
        ) from last_exc
