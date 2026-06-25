"""Доменные правила идентичности и конфликтов (ADR-0002). Без Django и IO.

Объект считается тем же, если совпадают water_source + name + year_built И его
координаты находятся в радиусе ≤100 м (пространственная часть проверяется на слое
persistence через PostGIS ST_DWithin). Здесь — ключ и сравнение значений на конфликт.
"""

from __future__ import annotations

import math
from typing import Any

# Поля, образующие ключ идентичности.
IDENTITY_FIELDS = ("water_source", "name", "year_built")

# Не участвуют в сравнении значений: сам ключ и координаты (их близость — отдельная
# пространственная проверка, а не «расхождение значения»).
_COMPARE_EXCLUDED = set(IDENTITY_FIELDS) | {"latitude", "longitude"}

_FLOAT_TOL = 1e-9


def identity_label(fields: dict) -> str:
    """Человекочитаемый ключ записи для отчёта о конфликтах."""
    return " | ".join(str(fields.get(f, "")) for f in IDENTITY_FIELDS)


def _values_equal(a: Any, b: Any) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=_FLOAT_TOL, abs_tol=_FLOAT_TOL)
    return a == b


def find_conflicts(incoming: dict, existing: dict, *, sheet: str) -> list[dict]:
    """Поля, где входящая запись расходится с уже существующей.

    Сравниваются только поля, которые есть в обеих записях с непустыми значениями.
    Возвращает по одной записи отчёта на каждое расхождение.
    """
    key = identity_label(incoming)
    conflicts: list[dict] = []
    for field, incoming_value in incoming.items():
        if field in _COMPARE_EXCLUDED:
            continue
        if field not in existing:
            continue
        existing_value = existing[field]
        if existing_value is None:
            continue
        if not _values_equal(incoming_value, existing_value):
            conflicts.append(
                {
                    "key": key,
                    "field": field,
                    "existing": existing_value,
                    "incoming": incoming_value,
                    "sheet": sheet,
                }
            )
    return conflicts
