import json
import re
import logging
from abc import ABC, abstractmethod
from concurrent.futures import Future, as_completed
from pathlib import Path

from src.agent.ai_executor import get_ai_executor

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
    def _send_to_provider(self, system_prompt: str, articles_json: str) -> tuple[str, dict, str]:
        """Возвращает (content, usage_dict, model_name).

        usage_dict: {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
        """
        ...

    def filter_article(self, articles: dict, context: dict) -> tuple[dict, dict, str]:
        """Возвращает (response_dict, total_usage, model_name).

        response_dict: {high_match: [...], medium_match: [...], low_match: [...]}
        total_usage: {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
        model_name: строка с именем модели ИИ
        """
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
            .replace("{field_knowledge}", context.get("field_knowledge", ""))
            .replace("{target_theme}", context.get("target_theme", ""))
            .replace("{target_context}", context.get("target_context", ""))
            .replace("{t_language}", context.get("language", "russian"))
        )
        logger.info("Системный промпт сформирован (%d символов)", len(system_prompt))

        chunks = [articles_for_ai[i:i + CHUNK_SIZE] for i in range(0, len(articles_for_ai), CHUNK_SIZE)]
        logger.info("Разбито на %d чанков по %d статей", len(chunks), CHUNK_SIZE)

        response: dict[str, list] = {k: [] for k in MATCH_KEYS}
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        model_name = ""

        try:
            self.create_agent()
            executor = get_ai_executor()

            index_to_future: dict[int, Future[tuple[str, dict, str]]] = {
                idx: executor.submit(
                    self._send_to_provider,
                    system_prompt,
                    json.dumps(chunk, ensure_ascii=False),
                )
                for idx, chunk in enumerate(chunks)
            }
            logger.info("Отправлено %d задач в AI executor", len(index_to_future))

            results: dict[int, dict] = {}
            for future in as_completed(index_to_future.values()):
                idx = next(i for i, f in index_to_future.items() if f is future)
                try:
                    raw, usage, m_name = future.result()
                    logger.info("Ответ чанка %d получен (%d символов)", idx, len(raw))
                    results[idx] = self._parse_ai_response(raw)
                    total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                    total_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                    total_usage["total_tokens"] += usage.get("total_tokens", 0)
                    if not model_name:
                        model_name = m_name
                except Exception:
                    logger.exception("Ошибка при обработке чанка %d, пропускаю", idx)
                    results[idx] = {}

            for idx in range(len(chunks)):
                parsed = results.get(idx, {})
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
        logger.info("Использовано токенов: prompt=%d, completion=%d, total=%d",
                     total_usage["prompt_tokens"], total_usage["completion_tokens"],
                     total_usage["total_tokens"])

        return response, total_usage, model_name

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
                    "publish_name": orig.get("publish_name"),
                    "publish_link": orig.get("publish_link"),
                    "citation": orig.get("citation"),
                }
