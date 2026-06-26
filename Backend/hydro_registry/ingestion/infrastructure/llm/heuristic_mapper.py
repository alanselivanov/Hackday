"""Оффлайн-маппер по ключевым словам — для демо/тестов без OpenRouter.

Включается переменной окружения INGESTION_FAKE_MAPPER (см. factory). Тип сооружения
определяется по заголовку листа, колонки — по подстрокам в их именах. Это упрощённая
замена LLM: точность ниже, но работает без сети и ключа.
"""

from __future__ import annotations

from ...application.ports import SchemaMapper
from ...domain.field_catalog import fields_for
from ...domain.types import ColumnSample, MappingResult

# Тип сооружения по ключевым словам в заголовке/имени листа.
_TYPE_KEYWORDS = [
    ("шлюз", "sluice"),
    ("водозабор", "intake"),
    ("насос", "pumping"),
    ("плотин", "dam_dyke"),
    ("дамб", "dam_dyke"),
    ("пост", "post"),
    ("канал", "canal"),
]

# (поле, требуемые подстроки) — порядок важен: более специфичные правила выше.
_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("facility_type", ("тип", "объект")),
    ("district", ("район",)),
    ("name", ("наименован",)),
    ("name", ("название",)),
    ("water_source", ("водоисточник",)),
    ("water_source", ("источник",)),
    ("year_balanced", ("баланс",)),
    ("year_built", ("год", "ввод")),
    ("year_built", ("год",)),
    # detected_wear_override ДО wear_percentage: «износ по осмотру» специфичнее «износа».
    ("detected_wear_override", ("износ", "осмотр")),
    ("wear_percentage", ("износ",)),
    ("efficiency_fact", ("факт",)),
    ("efficiency_project", ("проект",)),
    ("efficiency_project", ("кпд",)),
    ("technical_condition", ("состояни",)),
    ("cadastral_number", ("кадастр",)),
    ("state_act", ("акт",)),
    ("uid", ("реестр",)),
    ("latitude", ("широта",)),
    ("longitude", ("долгота",)),
    # Паспортные поля для расчёта периода осмотра / эскалации статуса (ADR-0004).
    ("safety_class", ("класс",)),
    ("design_service_life", ("срок", "служб")),
    ("is_seasonal_risk", ("сезон",)),
    ("is_seasonal_risk", ("паводок",)),
    ("has_pressure_front", ("напорн",)),
    ("is_emergency_prone", ("аварийност",)),
    # Осмотровые поля → InspectionLog. Порядок важен для пар с общей подстрокой.
    ("inspection_date", ("дата", "осмотр")),
    ("inspection_type", ("тип", "осмотр")),
    ("inspector_name", ("инспектор",)),
    ("inspector_name", ("фио",)),
    ("crack_width", ("раскрыти",)),            # ДО crack_criticality
    ("crack_criticality", ("критичн", "трещин")),
    ("crack_criticality", ("трещин",)),
    ("filtration_rate", ("расход", "фильтрац")),  # ДО has_filtration
    ("has_filtration", ("фильтрац",)),
    ("deformation_value", ("смещени",)),
    ("deformation_value", ("просадк",)),
    ("has_deformation", ("деформац",)),
    ("siltation_percentage", ("заилен",)),
    ("equipment_malfunction", ("поломк",)),
    ("equipment_malfunction", ("неисправн",)),
    # канал
    ("earth_length", ("землян",)),
    ("lined_length", ("облиц",)),
    ("total_length", ("протяж",)),
    ("area_regular", ("регулярн",)),
    ("area_liman", ("лиман",)),
    ("area_flooded", ("обводн",)),
    ("bottom_width", ("ширин", "дну")),
    ("top_width", ("ширин", "верх")),
    ("depth", ("глубин",)),
    ("capacity", ("пропускн",)),
    ("capacity", ("способност",)),
    # шлюз
    ("gate_type", ("тип", "затвор")),
    ("gates_count", ("затвор",)),
    ("drive_type", ("привод",)),
    ("max_discharge", ("сброс",)),
    # водозабор
    ("intake_type", ("тип", "водозабор")),
    ("is_gravity", ("самотечн",)),
    ("fish_protection", ("рыбозащит",)),
    ("max_volume_clean", ("объ", "забор")),
    # насосная станция
    ("pumps_count", ("насос",)),
    ("installed_power", ("мощност",)),
    ("current_consumption", ("расход", "энерг")),
    ("head_pressure", ("напор",)),
    # плотина/дамба
    ("material", ("материал",)),
    ("crest_length", ("гребн",)),
    ("max_height", ("высота",)),
    ("reservoir_volume", ("водохранилищ",)),
    ("is_declared_dangerous", ("аварийн",)),
    # гидропост
    ("post_type", ("тип", "пост")),
    ("equipment_installed", ("датчик",)),
    ("equipment_installed", ("эхолот",)),
    ("current_water_level", ("текущ", "уровень")),
    ("critical_water_level", ("критическ",)),
]


def _detect_type(facility_hint: str) -> str:
    text = (facility_hint or "").lower()
    for keyword, facility_type in _TYPE_KEYWORDS:
        if keyword in text:
            return facility_type
    return "canal"


class HeuristicSchemaMapper(SchemaMapper):
    def map(self, *, facility_hint: str, columns: list[ColumnSample]) -> MappingResult:
        facility_type = _detect_type(facility_hint)
        valid_fields = {spec.name for spec in fields_for(facility_type)}

        mapping: dict[int, str] = {}
        used: set[str] = set()
        for column in columns:
            name = column.name.lower()
            for field, keywords in _RULES:
                if field in valid_fields and field not in used and all(k in name for k in keywords):
                    mapping[column.index] = field
                    used.add(field)
                    break
        return MappingResult(facility_type=facility_type, mapping=mapping)
