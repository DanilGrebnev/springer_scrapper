"""
Распаковывает вложенный объект original в родительский объект статьи.
Используется для трансформации result_*.json файлов.
"""

import json
from pathlib import Path


def flatten_original(path: Path) -> None:
    """Распаковывает original в каждый объект статей в high_match, medium_match, low_match."""
    data = json.loads(path.read_text(encoding="utf-8"))

    ai_result = data.get("ai_result", data)
    for key in ("high_match", "medium_match", "low_match"):
        for item in ai_result.get(key, []):
            if "original" in item:
                item.update(item.pop("original"))

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    path = Path(__file__).resolve().parent.parent / "results" / "result_2026-03-24_02-49-27.json"
    flatten_original(path)
    print("Done.")
