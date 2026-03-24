import json
import re
import logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "agent" / "prompts" / "prompt.txt"
CHUNK_SIZE = 5
MATCH_KEYS = ("high_match", "medium_match", "low_match")


class AIClient(ABC):

    @abstractmethod
    def create_agent(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def _send_to_provider(self, system_prompt: str, articles_json: str) -> str:
        ...

    def send_message(self, articles: dict, context: dict) -> dict:
        articles_for_ai = []
        articles_by_id: dict[str, dict] = {}

        for page_articles in articles.values():
            for a in page_articles:
                articles_for_ai.append({
                    "id": a["id"],
                    "title": a["title"],
                    "description": a.get("description", ""),
                    "abstract": a.get("abstract", ""),
                })
                articles_by_id[a["id"]] = a

        logger.info("Подготовлено %d статей для ИИ", len(articles_for_ai))

        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        system_prompt = (
            prompt_template
            .replace("{target_theme}", context.get("title", ""))
            .replace("{target_context}", context.get("description", ""))
            .replace("{more_context}", context.get("abstract_description", ""))
            .replace("{t_language}", context.get("language", "russian"))
        )
        logger.info("Системный промпт сформирован (%d символов)", len(system_prompt))

        chunks = [articles_for_ai[i:i + CHUNK_SIZE] for i in range(0, len(articles_for_ai), CHUNK_SIZE)]
        logger.info("Разбито на %d чанков по %d статей", len(chunks), CHUNK_SIZE)

        response: dict[str, list] = {k: [] for k in MATCH_KEYS}

        try:
            self.create_agent()

            for idx, chunk in enumerate(chunks, 1):
                logger.info("--- Чанк %d/%d (%d статей) ---", idx, len(chunks), len(chunk))
                chunk_json = json.dumps(chunk, ensure_ascii=False)
                raw = self._send_to_provider(system_prompt, chunk_json)
                logger.info("Ответ чанка %d получен (%d символов)", idx, len(raw))

                parsed = self._parse_ai_response(raw)
                for key in MATCH_KEYS:
                    response[key].extend(parsed.get(key, []))

        finally:
            self.close()
            logger.info("Агент закрыт")

        self._enrich_with_originals(response, articles_by_id)

        total = sum(len(v) for v in response.values())
        logger.info("Итого: %d совпадений (high=%d, medium=%d, low=%d)",
                     total, len(response["high_match"]),
                     len(response["medium_match"]), len(response["low_match"]))

        return response

    @staticmethod
    def _parse_ai_response(raw: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        logger.warning("Не удалось распарсить ответ ИИ, пропускаю чанк")
        return {}

    @staticmethod
    def _enrich_with_originals(response: dict, articles_by_id: dict[str, dict]) -> None:
        for key in MATCH_KEYS:
            for item in response[key]:
                orig = articles_by_id.get(item.get("id", ""), {})
                item["original"] = {
                    "title": orig.get("title"),
                    "link": orig.get("link"),
                    "description": orig.get("description"),
                    "abstract": orig.get("abstract"),
                    "authors": orig.get("authors"),
                    "published": orig.get("published"),
                    "publications_type": orig.get("publications_type"),
                    "is_access": orig.get("is_access"),
                }
