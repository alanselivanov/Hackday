"""Детерминированная раскладка строк по полям модели согласно карте LLM.

Здесь — никакого LLM: только приведение типов и применение карты к значениям.
"""

from __future__ import annotations

from typing import Any

from ..domain.field_catalog import fields_for
from ..domain.types import MappingResult, ParsedSheet


def coerce(raw: Any, field_type: str) -> Any:
    """Привести сырое значение ячейки к типу поля. Пусто/мусор → None."""
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = raw.strip()
        if raw == "":
            return None

    if field_type == "str":
        # Excel отдаёт числа как float; не превращаем идентификаторы в "123.0".
        if isinstance(raw, float) and raw.is_integer():
            return str(int(raw))
        return str(raw)
    if field_type == "int":
        try:
            return int(float(raw))
        except (ValueError, TypeError):
            return None
    if field_type in ("float", "coord"):
        try:
            return float(raw)
        except (ValueError, TypeError):
            return None
    if field_type == "bool":
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in ("1", "true", "да", "yes", "+")
    return None


def build_records(sheet: ParsedSheet, mapping_result: MappingResult) -> list[dict]:
    """Превратить строки листа в список dict значений полей по карте маппинга."""
    specs = {spec.name: spec for spec in fields_for(mapping_result.facility_type)}
    records: list[dict] = []
    for row in sheet.rows:
        record: dict = {}
        for col_index, field_name in mapping_result.mapping.items():
            spec = specs.get(field_name)
            if spec is None:
                continue
            raw = row[col_index] if col_index < len(row) else None
            value = coerce(raw, spec.type)
            if value is not None:
                record[field_name] = value
        # Пустые/хвостовые строки листа не порождают записей.
        if record:
            records.append(record)
    return records


def unmapped_column_names(sheet: ParsedSheet, mapping_result: MappingResult) -> list[str]:
    """Имена колонок, которые LLM не сопоставил ни с одним полем."""
    mapped = set(mapping_result.mapping.keys())
    return [col.name for col in sheet.columns if col.index not in mapped]
