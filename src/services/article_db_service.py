import logging

from src.db.models.article import Article
from src.db.models.artical_match import ArticalMatch
from src.db.models.result_request import ResultRequest
from src.db.models.request import Request

logger = logging.getLogger(__name__)

MATCH_KEYS = ("high_match", "medium_match", "low_match")


async def save_scraped_articles(articles: dict) -> dict[str, Article]:
    """Сохраняет статьи из скрапинга в Article. Дедупликация по link.

    Возвращает маппинг scraper_id -> Article (ORM-объект с реальным PK).
    """
    articles_map: dict[str, Article] = {}

    for page_articles in articles.values():
        for a in page_articles:
            link = a.get("link", "")
            scraper_id = a.get("id", "")

            if not link:
                continue

            existing = await Article.filter(link=link).first()
            if existing:
                articles_map[scraper_id] = existing
                continue

            article = await Article.create(
                title=a.get("title", ""),
                link=link,
                description=a.get("description", ""),
                abstract=a.get("abstract", ""),
                publications_type=a.get("publications_type", ""),
                authors=a.get("authors", ""),
                published=a.get("published", ""),
                open_access=bool(a.get("is_access", False)),
                publish_name=a.get("publish_name", ""),
                publish_link=a.get("publish_link", ""),
            )
            articles_map[scraper_id] = article

    logger.info("Сохранено / найдено %d статей в Article", len(articles_map))
    return articles_map


async def save_analysis_result(
    ai_response: dict,
    articles_map: dict[str, Article],
    usage: dict,
    model_name: str,
    request_obj: Request,
) -> ResultRequest:
    """Сохраняет результат ИИ-анализа: ArticalMatch + ResultRequest + связи."""

    # 1. Создать ResultRequest
    result_req = await ResultRequest.create(
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        response_model=model_name,
    )

    # 2. Для каждой классифицированной статьи создать ArticalMatch
    match_records: list[ArticalMatch] = []
    for level_key in MATCH_KEYS:
        for item in ai_response.get(level_key, []):
            scraper_id = item.get("id", "")
            article_obj = articles_map.get(scraper_id)
            if article_obj is None:
                logger.warning("Статья scraper_id=%s не найдена в articles_map, пропускаю", scraper_id)
                continue

            match_rec = await ArticalMatch.create(
                original_artical=article_obj,
                level_match=level_key,
                comparison_of_rules=item.get("comparison_of_rules"),
                explanation=item.get("explanation", ""),
                t_title=item.get("t_title", ""),
                t_abstract=item.get("t_abstract", ""),
            )
            match_records.append(match_rec)

    # 3. Связать ArticalMatch -> ResultRequest через MtM
    if match_records:
        await result_req.articles.add(*match_records)

    # 4. Связать Request -> ResultRequest через MtM
    await request_obj.results.add(result_req)

    logger.info(
        "ResultRequest(%d) создан: %d matches, tokens=%d, model=%s",
        result_req.pk, len(match_records), result_req.total_tokens, model_name,
    )
    return result_req


async def build_result_from_db(request_obj: Request) -> dict:
    """Собирает JSON-результат из БД в формате {high_match, medium_match, low_match}.

    Цепочка: Request -> results -> ResultRequest -> articles -> ArticalMatch -> Article
    """
    result: dict[str, list] = {k: [] for k in MATCH_KEYS}

    result_requests = await request_obj.results.all()
    for rr in result_requests:
        matches = await rr.articles.all().prefetch_related("original_artical")
        for match in matches:
            article = match.original_artical
            entry = {
                "id": match.pk,
                "t_title": match.t_title,
                "t_abstract": match.t_abstract,
                "explanation": match.explanation,
                "comparison_of_rules": match.comparison_of_rules,
                "level_match": match.level_match,
                "original": {
                    "title": article.title,
                    "link": article.link,
                    "description": article.description,
                    "abstract": article.abstract,
                    "authors": article.authors,
                    "published": article.published,
                    "publications_type": article.publications_type,
                    "is_access": article.open_access,
                    "publish_name": article.publish_name,
                    "publish_link": article.publish_link,
                },
            }
            level = match.level_match
            if level in result:
                result[level].append(entry)

    return result
