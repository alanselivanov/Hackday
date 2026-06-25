"""Реальный LLM-адаптер на OpenRouter (ADR-0003).

Пакет ``openrouter`` импортируется лениво внутри метода, чтобы приложение и тесты
загружались без установленного пакета и без ключа (тесты подменяют порт фейком).
"""

from __future__ import annotations

import json
import os

from ...application.ports import SchemaMapper
from ...domain.field_catalog import full_catalog_prompt
from ...domain.types import ColumnSample, MappingResult

_MODEL = "openrouter/auto"


def _api_key() -> str:
    # В проектном .env ключ называется OPEN_ROUTER; поддерживаем и стандартное имя.
    return os.getenv("OPENROUTER_API_KEY") or os.getenv("OPEN_ROUTER", "")


def _build_prompt(facility_hint: str, columns: list[ColumnSample]) -> str:
    column_lines = []
    for col in columns:
        samples = ", ".join(str(s) for s in col.samples)
        column_lines.append(f"[{col.index}] «{col.name}» — примеры: {samples}")
    columns_block = "\n".join(column_lines)
    fields_block = full_catalog_prompt()
    return (
        "Ты сопоставляешь колонки таблицы гидротехнических сооружений с полями реестра.\n"
        "НЕ придумывай значения. Работай только с именами колонок и примерами.\n"
        "Если колонка не подходит ни под одно поле — не включай её в mapping.\n\n"
        f"Заголовок/контекст листа: {facility_hint}\n\n"
        "Доступные поля (имя, тип, описание):\n"
        f"{fields_block}\n\n"
        "Колонки файла (индекс, имя, примеры):\n"
        f"{columns_block}\n\n"
        "Определи facility_type (один из: canal, sluice, intake, pumping, dam_dyke, post) "
        "по заголовку и набору колонок. Затем верни СТРОГО JSON вида:\n"
        '{"facility_type": "...", "mapping": {"<индекс колонки>": "<имя поля>"}}'
    )


class OpenRouterSchemaMapper(SchemaMapper):
    def map(self, *, facility_hint: str, columns: list[ColumnSample]) -> MappingResult:
        from openrouter import OpenRouter  # ленивый импорт (см. ADR-0003)

        prompt = _build_prompt(facility_hint, columns)
        with OpenRouter(api_key=_api_key()) as client:
            response = client.chat.send(
                model=_MODEL,
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            )
        content = response.choices[0].message.content
        return self._parse(content)

    @staticmethod
    def _parse(content: str) -> MappingResult:
        # LLM нередко оборачивает JSON в ```-блок или добавляет текст — берём {...}.
        start, end = content.find("{"), content.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("LLM вернул ответ без JSON-объекта.")
        data = json.loads(content[start : end + 1])

        mapping = {}
        for key, value in (data.get("mapping") or {}).items():
            try:
                mapping[int(key)] = str(value)
            except (ValueError, TypeError):
                continue  # пропускаем некорректные пары, не роняя импорт
        # Пустой/незнакомый facility_type отсеется валидацией в ImportService.
        return MappingResult(facility_type=str(data.get("facility_type", "")), mapping=mapping)
