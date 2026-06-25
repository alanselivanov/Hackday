"""Каталог целевых полей реестра — вход в промпт LLM и источник правил приведения типов.

LLM сопоставляет имена колонок файла с этими полями; значения раскладывает код
(см. ADR-0001). Координаты приходят отдельными псевдополями ``latitude``/``longitude``
и собираются в ``location`` (PointField) на слое persistence.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldSpec:
    name: str       # имя поля модели (или псевдополя latitude/longitude)
    label: str      # русское описание для промпта
    type: str       # 'str' | 'int' | 'float' | 'bool' | 'coord'


# Общие поля BaseHydroFacility — есть у всех типов сооружений.
BASE_FIELDS: list[FieldSpec] = [
    FieldSpec("uid", "Регистрационный номер", "float"),
    FieldSpec("name", "Наименование сооружения", "str"),
    FieldSpec("water_source", "Водоисточник", "str"),
    FieldSpec("district", "Название обслуживаемого района", "str"),
    FieldSpec("rural_district", "Сельский округ", "str"),
    FieldSpec("cadastral_number", "Кадастровый номер", "str"),
    FieldSpec("state_act", "Государственный акт", "str"),
    FieldSpec("year_built", "Год ввода в эксплуатацию", "int"),
    FieldSpec("year_balanced", "Год принятия на баланс", "int"),
    FieldSpec("wear_percentage", "Процент износа", "float"),
    FieldSpec("technical_condition", "Техническое состояние", "str"),
    FieldSpec("efficiency_project", "КПД проектный", "float"),
    FieldSpec("efficiency_fact", "КПД фактический", "float"),
    FieldSpec("is_emergency_prone", "Флаг повышенной аварийности", "bool"),
]

# Координаты — отдельные входные псевдополя, собираются в location.
COORDINATE_FIELDS: list[FieldSpec] = [
    FieldSpec("latitude", "Широта", "coord"),
    FieldSpec("longitude", "Долгота", "coord"),
]

# Поля подклассов. На срезе #01 реализован только канал.
CANAL_FIELDS: list[FieldSpec] = [
    FieldSpec("capacity", "Пропускная способность, м3/с", "float"),
    FieldSpec("total_length", "Всего протяжённость, км", "float"),
    FieldSpec("earth_length", "Земляное русло, км", "float"),
    FieldSpec("lined_length", "Облицованное русло, км", "float"),
    FieldSpec("area_regular", "Подвешенная площадь: регулярное орошение, га", "float"),
    FieldSpec("area_liman", "Лиманное орошение, га", "float"),
    FieldSpec("area_flooded", "Обводнённое, га", "float"),
    FieldSpec("bottom_width", "Ширина по дну, м", "float"),
    FieldSpec("top_width", "Ширина по верху, м", "float"),
    FieldSpec("depth", "Глубина, м", "float"),
]

# Специфические поля по типу сооружения (расширяется в срезе #07).
SUBCLASS_FIELDS: dict[str, list[FieldSpec]] = {
    "canal": CANAL_FIELDS,
}

SUPPORTED_FACILITY_TYPES = tuple(SUBCLASS_FIELDS.keys())


def fields_for(facility_type: str) -> list[FieldSpec]:
    """Все целевые поля для типа: общие + специфические + координаты."""
    return BASE_FIELDS + SUBCLASS_FIELDS.get(facility_type, []) + COORDINATE_FIELDS


def catalog_prompt(facility_type: str) -> str:
    """Текстовое описание полей для промпта LLM."""
    lines = [f"- {spec.name} ({spec.type}): {spec.label}" for spec in fields_for(facility_type)]
    return "\n".join(lines)
