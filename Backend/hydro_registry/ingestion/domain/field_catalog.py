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
SLUICE_FIELDS: list[FieldSpec] = [
    FieldSpec("gates_count", "Количество затворов/сооружений", "int"),
    FieldSpec("gate_type", "Тип затвора", "str"),
    FieldSpec("drive_type", "Привод затвора (электрический, механический, ручной)", "str"),
    FieldSpec("max_discharge", "Максимальный сброс воды, м3/с", "float"),
]

INTAKE_FIELDS: list[FieldSpec] = [
    FieldSpec("intake_type", "Тип водозабора (береговой, русловой, плавучий)", "str"),
    FieldSpec("is_gravity", "Самотечный (да) или механический (нет)", "bool"),
    FieldSpec("fish_protection", "Наличие рыбозащитных устройств", "bool"),
    FieldSpec("max_volume_clean", "Проектный объём забора воды", "float"),
]

PUMPING_FIELDS: list[FieldSpec] = [
    FieldSpec("pumps_count", "Количество установленных насосов", "int"),
    FieldSpec("installed_power", "Суммарная мощность электродвигателей, кВт", "float"),
    FieldSpec("current_consumption", "Фактический расход энергии", "float"),
    FieldSpec("head_pressure", "Напор насосной станции, м водного столба", "float"),
]

DAM_FIELDS: list[FieldSpec] = [
    FieldSpec("material", "Материал сооружения (земляная, бетонная, каменно-набросная)", "str"),
    FieldSpec("crest_length", "Длина по гребню, м", "float"),
    FieldSpec("max_height", "Максимальная высота сооружения, м", "float"),
    FieldSpec("reservoir_volume", "Объём удерживаемого водохранилища, млн м3", "float"),
    FieldSpec("is_declared_dangerous", "Относится ли к декларируемым аварийным объектам", "bool"),
]

# Гидропост: телеметрические поля. last_telemetry_at (время пинга) — рантайм-данные,
# а не характеристики из файла-паспорта, поэтому в импорт-каталог не включаем.
POST_FIELDS: list[FieldSpec] = [
    FieldSpec("post_type", "Тип поста (автоматический / ручной)", "str"),
    FieldSpec("equipment_installed", "Модель датчика/эхолота", "str"),
    FieldSpec("current_water_level", "Текущий уровень воды, см", "float"),
    FieldSpec("critical_water_level", "Критический уровень для оповещения, см", "float"),
]

# Специфические поля по типу сооружения.
SUBCLASS_FIELDS: dict[str, list[FieldSpec]] = {
    "canal": CANAL_FIELDS,
    "sluice": SLUICE_FIELDS,
    "intake": INTAKE_FIELDS,
    "pumping": PUMPING_FIELDS,
    "dam_dyke": DAM_FIELDS,
    "post": POST_FIELDS,
}

SUPPORTED_FACILITY_TYPES = tuple(SUBCLASS_FIELDS.keys())


def fields_for(facility_type: str) -> list[FieldSpec]:
    """Все целевые поля для типа: общие + специфические + координаты."""
    return BASE_FIELDS + SUBCLASS_FIELDS.get(facility_type, []) + COORDINATE_FIELDS


def _format(specs: list[FieldSpec]) -> str:
    return "\n".join(f"- {spec.name} ({spec.type}): {spec.label}" for spec in specs)


def catalog_prompt(facility_type: str) -> str:
    """Текстовое описание полей конкретного типа для промпта LLM."""
    return _format(fields_for(facility_type))


def full_catalog_prompt() -> str:
    """Полный каталог по всем типам — LLM сам определяет тип, поэтому видит все поля."""
    blocks = ["Общие поля (для всех типов сооружений):", _format(BASE_FIELDS)]
    for facility_type, specs in SUBCLASS_FIELDS.items():
        blocks.append(f"Поля для типа «{facility_type}»:")
        blocks.append(_format(specs))
    blocks.append("Координаты:")
    blocks.append(_format(COORDINATE_FIELDS))
    return "\n".join(blocks)
