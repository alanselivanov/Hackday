"""Чистые доменные типы фичи импорта. Без зависимостей от Django и IO."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ColumnSample:
    """Колонка распознанного листа: индекс, флэт-имя и до 3 сэмплов значений."""

    index: int
    name: str
    samples: list[Any] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedSheet:
    """Один лист (или плоский CSV), приведённый к колонкам + строкам данных."""

    name: str
    columns: list[ColumnSample]
    rows: list[list[Any]]  # каждая строка выровнена по индексам columns


@dataclass(frozen=True)
class MappingResult:
    """Ответ LLM-порта: тип сооружения + карта «индекс колонки → поле модели»."""

    facility_type: str
    mapping: dict[int, str]


@dataclass
class ImportReport:
    """Отчёт об импорте — тело ответа endpoint'а."""

    created: int = 0
    skipped_duplicates: int = 0
    conflicts: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unmapped_columns: list[str] = field(default_factory=list)
    # По записи на каждое созданное сооружение: что загрузилось + статус ремонта
    # (модуль 6) + период осмотра (модуль 5) с обоснованием. Заполняется слоем
    # persistence (ADR-0004); фейковые репозитории в юнит-тестах его не наполняют.
    facilities: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "created": self.created,
            "skipped_duplicates": self.skipped_duplicates,
            "conflicts": self.conflicts,
            "warnings": self.warnings,
            "unmapped_columns": self.unmapped_columns,
            "facilities": self.facilities,
        }
