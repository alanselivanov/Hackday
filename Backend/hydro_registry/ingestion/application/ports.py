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
    """Порт хранилища: поиск дубля по ключу идентичности и создание записи."""

    @abstractmethod
    def find_match(self, *, facility_type: str, fields: dict) -> dict | None:
        """Существующая запись по ключу идентичности (water_source+name+year_built
        И координаты ≤100 м) как dict значений полей, либо None если совпадения нет."""
        ...

    @abstractmethod
    def create(self, *, facility_type: str, fields: dict) -> dict | None:
        """Создаёт сооружение (и, при наличии findings, осмотр + аналитику).
        Возвращает per-facility результат для отчёта (см. ADR-0004) или None,
        если реализация не собирает детали (например, фейк в юнит-тестах)."""
        ...
