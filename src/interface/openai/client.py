import os
import logging
from openai import OpenAI
from src.interface.base import AIClient

logger = logging.getLogger(__name__)


class OpenAIClient(AIClient):

    def __init__(self):
        self._client: OpenAI | None = None
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._temperature = float(os.getenv("AI_TEMPERATURE", "0.7"))

    def create_agent(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        self._client = OpenAI(api_key=api_key)
        logger.info("OpenAI клиент создан (model=%s, temperature=%s)", self._model, self._temperature)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("OpenAI клиент закрыт")

    def _send_to_provider(self, system_prompt: str, articles_json: str) -> str:
        if self._client is None:
            raise RuntimeError("Agent not created. Call create_agent() first.")

        response = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": articles_json},
            ],
        )

        return response.choices[0].message.content or ""

    def test_connection(self) -> str:
        """Простой тестовый запрос для проверки доступа к API."""
        if self._client is None:
            raise RuntimeError("Agent not created. Call create_agent() first.")

        response = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            messages=[
                {"role": "user", "content": "Say hello in one sentence."},
            ],
        )

        return response.choices[0].message.content or ""
