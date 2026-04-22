"""Сервис рендера PDF-отчёта по Request.

Рендер идёт через headless Chrome + CDP Page.printToPDF.
Chrome у нас уже есть и в локале (для скраппинга), и в docker-образе api.
Благодаря этому не нужны дополнительные heavyweight-зависимости
(WeasyPrint/GTK, reportlab + отдельные TTF-шрифты с кириллицей и т.п.).

Публичный API:
    await render_request_pdf(request_obj) -> bytes
"""

from __future__ import annotations

import asyncio
import base64
import html as html_lib
import logging
from typing import Any
from urllib.parse import quote

from src.db.models.request import Request
from src.scrapper.chrome_factory import ChromeFactory
from src.services.article_db_service import build_result_from_db

logger = logging.getLogger(__name__)

MATCH_SECTIONS = [
    ("high_match", "Высокое совпадение", "high"),
    ("medium_match", "Среднее совпадение", "medium"),
    ("low_match", "Низкое совпадение", "low"),
]


# --------------------------------------------------------------------- HTML

_CSS = """
* { box-sizing: border-box; }
html, body {
    margin: 0;
    padding: 0;
    font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1f2937;
    font-size: 11pt;
    line-height: 1.45;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}
.page {
    padding: 24px 28px;
}
h1.doc-title {
    font-size: 22pt;
    margin: 0 0 18px 0;
    color: #111827;
    font-weight: 700;
}
h2.section-label {
    font-size: 13pt;
    margin: 22px 0 10px 0;
    color: #111827;
    font-weight: 600;
}
.pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 14px;
}
.pill {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 999px;
    background: #f0f0f0;
    color: #1f2937;
    font-size: 10pt;
    border: 1px solid #e3e3e3;
}
.disclosure-box {
    background: #fafafa;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 18px;
    font-size: 10.5pt;
}
.disclosure-box .label {
    font-weight: 600;
    color: #111827;
    margin-bottom: 6px;
}
/* Заголовки секций совпадений */
.match-heading {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14pt;
    font-weight: 700;
    margin: 26px 0 12px 0;
    page-break-after: avoid;
}
.match-heading .count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 26px;
    height: 26px;
    padding: 0 8px;
    border-radius: 999px;
    background: rgba(0,0,0,0.08);
    color: inherit;
    font-size: 10.5pt;
    font-weight: 600;
}
.match-heading.high   { color: #1f8a4c; }
.match-heading.medium { color: #c77a00; }
.match-heading.low    { color: #c0392b; }

/* Карточка статьи */
.card {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 14px;
    page-break-inside: avoid;
    background: #ffffff;
}
.card .article-id {
    font-size: 9pt;
    color: #6b7280;
    margin-bottom: 6px;
}
.card .article-title {
    font-size: 12pt;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 10px;
    line-height: 1.3;
}
.card .article-abstract {
    font-size: 10.5pt;
    color: #1f2937;
    margin-bottom: 12px;
    white-space: pre-wrap;
}
.card .article-authors {
    font-size: 10pt;
    color: #4b5563;
    margin-bottom: 8px;
}
.card .original-link {
    display: inline-block;
    margin-bottom: 12px;
    color: #0f172a;
    font-weight: 600;
    text-decoration: underline;
    font-size: 10pt;
}
.block {
    background: #f7f7f8;
    border: 1px solid #ececf0;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 10px;
}
.block .block-label {
    font-size: 9pt;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
    font-weight: 600;
}
.block .block-body {
    font-size: 10.5pt;
    color: #1f2937;
    white-space: pre-wrap;
    word-break: break-word;
}
.rules-label {
    font-size: 10pt;
    font-weight: 600;
    color: #111827;
    margin: 4px 0 8px 0;
}
table.rules {
    width: 100%;
    border-collapse: collapse;
    font-size: 10pt;
}
table.rules thead th {
    text-align: left;
    font-weight: 600;
    color: #111827;
    background: #f3f4f6;
    padding: 8px 10px;
    border-bottom: 1px solid #e5e7eb;
}
table.rules tbody td {
    padding: 8px 10px;
    vertical-align: top;
    border-bottom: 1px solid #eef0f3;
    color: #1f2937;
}
table.rules tbody tr:last-child td {
    border-bottom: none;
}
table.rules td.rule-col {
    width: 30%;
}
"""


def _esc(value: Any) -> str:
    return html_lib.escape("" if value is None else str(value))


def _pill(text: str) -> str:
    return f'<span class="pill">{_esc(text)}</span>'


def _filters_pills(request_obj: Request) -> str:
    pills: list[str] = []
    if request_obj.field_knowledge:
        pills.append(_pill(f"Область знаний (направление): {request_obj.field_knowledge}"))
    if request_obj.target_theme:
        pills.append(_pill(f"Целевая тема: {request_obj.target_theme}"))
    if request_obj.language:
        pills.append(_pill(f"Language: {request_obj.language}"))
    if request_obj.theme:
        pills.append(_pill(f"Поиск на тему: {request_obj.theme}"))
    if request_obj.date_from:
        pills.append(_pill(f"Год от: {request_obj.date_from}"))
    if request_obj.date_to:
        pills.append(_pill(f"Год до: {request_obj.date_to}"))
    pills.append(_pill(f"В открытом доступе: {'Да' if request_obj.open_access else 'Нет'}"))
    return '<div class="pills">' + "".join(pills) + "</div>"


def _disclosure(request_obj: Request) -> str:
    if not (request_obj.target_context or "").strip():
        return ""
    return (
        '<div class="disclosure-box">'
        '<div class="label">Раскрытие темы:</div>'
        f'<div>{_esc(request_obj.target_context)}</div>'
        "</div>"
    )


def _rules_table(rules: Any) -> str:
    if not isinstance(rules, list) or not rules:
        return ""
    rows: list[str] = []
    for r in rules:
        if not isinstance(r, dict):
            continue
        rule = _esc(r.get("rule", ""))
        desc = _esc(r.get("description", ""))
        rows.append(
            f'<tr><td class="rule-col">{rule}</td><td>{desc}</td></tr>'
        )
    if not rows:
        return ""
    return (
        f'<div class="rules-label">Правила сравнения ({len(rows)})</div>'
        '<table class="rules">'
        "<thead><tr><th>Правило</th><th>Описание</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def _card(entry: dict, display_id: int) -> str:
    original = entry.get("original") or {}
    title = entry.get("t_title") or original.get("title", "")
    abstract = entry.get("t_abstract") or original.get("abstract", "")
    authors = original.get("authors", "")
    link = original.get("link", "")
    citation = original.get("citation", "")
    explanation = entry.get("explanation", "")
    rules = entry.get("comparison_of_rules")

    parts: list[str] = ['<div class="card">']
    parts.append(f'<div class="article-id">ID: {display_id}</div>')
    if title:
        parts.append(f'<div class="article-title">{_esc(title)}</div>')
    if abstract:
        parts.append(f'<div class="article-abstract">{_esc(abstract)}</div>')
    if authors:
        parts.append(f'<div class="article-authors">{_esc(authors)}</div>')
    if link:
        parts.append(
            f'<a class="original-link" href="{_esc(link)}">Оригинал статьи ↗</a>'
        )
    if citation:
        parts.append(
            '<div class="block">'
            '<div class="block-label">Цитирование</div>'
            f'<div class="block-body">{_esc(citation)}</div>'
            "</div>"
        )
    if explanation:
        parts.append(
            '<div class="block">'
            '<div class="block-label">Объяснение</div>'
            f'<div class="block-body">{_esc(explanation)}</div>'
            "</div>"
        )
    parts.append(_rules_table(rules))
    parts.append("</div>")
    return "".join(parts)


def _section(entries: list[dict], title: str, css_class: str, start_id: int) -> tuple[str, int]:
    count = len(entries)
    if count == 0:
        return "", start_id
    cards = []
    next_id = start_id
    for entry in entries:
        cards.append(_card(entry, next_id))
        next_id += 1
    html = (
        f'<div class="match-heading {css_class}">'
        f"<span>{_esc(title)}</span>"
        f'<span class="count">{count}</span>'
        "</div>"
        + "".join(cards)
    )
    return html, next_id


def _build_html(request_obj: Request, result: dict) -> str:
    sections_html: list[str] = []
    running_id = 1
    for key, title, css_class in MATCH_SECTIONS:
        section_html, running_id = _section(
            result.get(key, []) or [], title, css_class, running_id
        )
        sections_html.append(section_html)

    body = (
        '<div class="page">'
        '<h1 class="doc-title">Детализация поиска</h1>'
        '<h2 class="section-label">Параметры запроса</h2>'
        + _filters_pills(request_obj)
        + _disclosure(request_obj)
        + "".join(sections_html)
        + "</div>"
    )

    return (
        "<!doctype html>"
        '<html lang="ru"><head><meta charset="utf-8">'
        f"<title>Детализация поиска #{request_obj.pk}</title>"
        f"<style>{_CSS}</style>"
        "</head>"
        f"<body>{body}</body></html>"
    )


# --------------------------------------------------------------- PDF RENDER


def _html_to_pdf_sync(html: str) -> bytes:
    """Рендерит HTML в PDF через headless Chrome + CDP Page.printToPDF.

    Вызывающий код должен гарантировать, что метод исполняется не в event loop
    (обычно через asyncio.to_thread), т.к. Selenium синхронный.
    """
    factory = ChromeFactory()
    driver = factory.create(headless=True)
    try:
        data_url = "data:text/html;charset=utf-8," + quote(html)
        driver.get(data_url)
        result = driver.execute_cdp_cmd(
            "Page.printToPDF",
            {
                "printBackground": True,
                "preferCSSPageSize": False,
                "paperWidth": 8.27,   # A4 in inches
                "paperHeight": 11.69,
                "marginTop": 0.4,
                "marginBottom": 0.4,
                "marginLeft": 0.4,
                "marginRight": 0.4,
                "scale": 1.0,
            },
        )
        return base64.b64decode(result["data"])
    finally:
        try:
            driver.quit()
        except Exception:
            logger.exception("Не удалось корректно закрыть headless Chrome после рендера PDF")


async def render_request_pdf(request_obj: Request) -> bytes:
    """Высокоуровневая обёртка: строит HTML по Request + результатам БД
    и рендерит его в PDF-байты в отдельном потоке."""
    result = await build_result_from_db(request_obj)
    html = _build_html(request_obj, result)
    return await asyncio.to_thread(_html_to_pdf_sync, html)
