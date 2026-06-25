"""Порты (интерфейсы), от которых зависит use-case. Реализации — в infrastructure.

Держим их абстрактными, чтобы доменная оркестрация не знала ни про Django, ни про
конкретного LLM-провайдера, и чтобы их можно было подменять фейками в тестах.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain.types import ColumnSample, MappingResult


class SchemaMapper(ABC):
    """LLM-порт: по именам колонок + сэмплам возвращает тип и карту маппинга."""

    @abstractmethod
    def map(self, *, facility_hint: str, columns: list[ColumnSample]) -> MappingResult:
        ...


class FacilityRepository(ABC):
    """Порт записи: создаёт сооружение нужного типа из dict значений полей."""

    @abstractmethod
    def create(self, *, facility_type: str, fields: dict) -> None:
        ...
