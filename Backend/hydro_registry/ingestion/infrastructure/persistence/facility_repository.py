"""Запись сооружений через Django ORM. Единственное место, зависящее от GeoDjango.

Собирает координаты из псевдополей latitude/longitude в location (PointField).
Поддержаны все типы сооружений (#07). Кроме записи сооружения, при наличии в строке
данных осмотра создаёт InspectionLog и запускает оба расчётных модуля (ADR-0004):
  модуль 5 (период осмотра, inspection_service) → модуль 6 (статус ремонта, analytics).
"""

from __future__ import annotations

from datetime import date, datetime

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.utils import timezone

from analytics.models import FacilityAnalytics
from analytics.services import recalculate_status
from infrastructure.models import (
    Canal,
    DamsAndDykes,
    PumpingStation,
    Sluice,
    WaterIntake,
)
from inspection_service import run_for_facility
from monitoring.models import HydroPost, InspectionLog

from ...application.ports import FacilityRepository
from ...domain.field_catalog import (
    INSPECTION_FIELD_NAMES,
    facility_field_names,
)
from ...domain.identity import IDENTITY_FIELDS

_MODEL_BY_TYPE = {
    "canal": Canal,
    "sluice": Sluice,
    "intake": WaterIntake,
    "pumping": PumpingStation,
    "dam_dyke": DamsAndDykes,
    "post": HydroPost,
}

_MATCH_RADIUS_M = 100


def _json_safe(value):
    """Приводит значение к JSON-сериализуемому виду (даты → ISO-строка)."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _point_from(fields: dict) -> Point | None:
    latitude = fields.get("latitude")
    longitude = fields.get("longitude")
    if latitude is None or longitude is None:
        return None
    return Point(float(longitude), float(latitude), srid=4326)


class DjangoFacilityRepository(FacilityRepository):
    def find_match(self, *, facility_type: str, fields: dict) -> dict | None:
        model = _MODEL_BY_TYPE.get(facility_type)
        if model is None:
            return None

        # Полный ключ идентичности обязателен, иначе склейку не делаем.
        if any(not fields.get(name) for name in IDENTITY_FIELDS):
            return None
        point = _point_from(fields)
        if point is None:
            return None

        key_filter = {name: fields[name] for name in IDENTITY_FIELDS}
        # На геометрии с географическим SRID (4326) Django запрещает __dwithin с
        # Distance, поэтому используем __distance_lte: для геодезической геометрии
        # расстояние считается по сфероиду в МЕТРАХ (ST_Distance), см. ADR-0002.
        existing = (
            model.objects.filter(
                **key_filter, location__distance_lte=(point, D(m=_MATCH_RADIUS_M))
            ).first()
        )
        if existing is None:
            return None
        return self._to_fields(existing, facility_type)

    @staticmethod
    def _to_fields(instance, facility_type: str) -> dict:
        # Только паспортные поля сооружения — осмотровые на сооружении не живут
        # и не должны участвовать в сравнении на конфликт.
        result = {}
        for name in facility_field_names(facility_type):
            result[name] = getattr(instance, name, None)
        return result

    def create(self, *, facility_type: str, fields: dict) -> dict | None:
        model = _MODEL_BY_TYPE.get(facility_type)
        if model is None:
            raise ValueError(f"Неподдерживаемый тип сооружения: {facility_type}")

        # Разделяем строку на паспорт сооружения и findings осмотра (ADR-0004).
        # Сюда же передаются ВСЕ входные переменные модуля 6 (см. formula_for_part_6.md §1):
        #   • контекст объекта → facility_data → BaseHydroFacility:
        #       facility_type, wear_percentage, is_emergency_prone, has_pressure_front, safety_class;
        #   • findings осмотра → inspection_fields → InspectionLog:
        #       inspection_date, inspection_type, crack_criticality, has_filtration, filtration_rate,
        #       has_deformation, deformation_value, crack_width, equipment_malfunction,
        #       is_silted, siltation_percentage, detected_wear_override.
        #   • current_water_level (для типа 'post') приходит как поле HydroPost в facility_data;
        #   • SafetyCriterion (K1/K2, Источник А) файлом НЕ импортируется — задаётся в админке.
        inspection_fields = {
            k: v for k, v in fields.items() if k in INSPECTION_FIELD_NAMES
        }
        facility_data = {
            k: v
            for k, v in fields.items()
            if k not in INSPECTION_FIELD_NAMES and k not in ("latitude", "longitude")
        }

        point = _point_from(fields)
        if point is not None:
            facility_data["location"] = point

        facility = model.objects.create(facility_type=facility_type, **facility_data)

        # Осмотр создаём только если в строке реально есть хоть один признак.
        if inspection_fields:
            log_kwargs = dict(inspection_fields)
            log_kwargs.setdefault("inspection_date", timezone.localdate())
            log_kwargs.setdefault("inspector_name", "Импорт из файла")
            log_kwargs.setdefault("inspection_type", "planned")
            InspectionLog.objects.create(facility=facility, **log_kwargs)

        # Модуль 5 (период осмотра) ДО модуля 6 (статус): модуль 6 читает
        # next_inspection_date. Разграничение полей — ADR-0004 / inspection_service.
        inspection_result = run_for_facility(facility)
        analytics = FacilityAnalytics.objects.get(facility=facility)
        recalculate_status(analytics)

        return self._build_detail(
            facility=facility,
            facility_type=facility_type,
            facility_data=facility_data,
            inspection_fields=inspection_fields,
            analytics=analytics,
            inspection_result=inspection_result,
        )

    @staticmethod
    def _build_detail(
        *,
        facility,
        facility_type,
        facility_data,
        inspection_fields,
        analytics,
        inspection_result,
    ) -> dict:
        """Per-facility результат для отчёта/демо: что загрузилось + оба вердикта
        с обоснованием (ADR-0004)."""
        reason = analytics.repair_status_reason or {}
        loaded = {
            k: _json_safe(v)
            for k, v in {**facility_data, **inspection_fields}.items()
            if k != "location"
        }
        # Координаты показываем явными широтой/долготой, а не объектом location.
        if facility.location is not None:
            loaded["latitude"] = round(facility.location.y, 6)
            loaded["longitude"] = round(facility.location.x, 6)
        next_date = analytics.next_inspection_date
        return {
            "name": facility.name,
            "facility_type": facility_type,
            "loaded": loaded,
            "has_inspection": bool(inspection_fields),
            # Модуль 6 — нужен ли ремонт
            "repair_status": analytics.repair_status,
            "repair_status_display": analytics.get_repair_status_display(),
            "condition_score": analytics.condition_score,
            "requires_verification": analytics.requires_verification,
            "repair_reasons": reason.get("factors") or [],
            "repair_note": reason.get("note"),
            # Модуль 5 — как часто осматривать
            "inspection_interval_days": analytics.inspection_interval_days,
            "next_inspection_date": next_date.isoformat() if next_date else None,
            "inspection_factors": reason.get("inspection_factors"),
            "needs_first_inspection": inspection_result.needs_first_inspection,
        }
