"""Запись сооружений через Django ORM. Единственное место, зависящее от GeoDjango.

Собирает координаты из псевдополей latitude/longitude в location (PointField).
На срезе #01 поддержан только канал; остальные типы добавляются в #07.
"""

from __future__ import annotations

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from infrastructure.models import (
    Canal,
    DamsAndDykes,
    PumpingStation,
    Sluice,
    WaterIntake,
)
from monitoring.models import HydroPost

from ...application.ports import FacilityRepository
from ...domain.field_catalog import fields_for
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
        result = {}
        for spec in fields_for(facility_type):
            if spec.name in ("latitude", "longitude"):
                continue
            result[spec.name] = getattr(instance, spec.name, None)
        return result

    def create(self, *, facility_type: str, fields: dict) -> None:
        model = _MODEL_BY_TYPE.get(facility_type)
        if model is None:
            raise ValueError(f"Неподдерживаемый тип сооружения: {facility_type}")

        point = _point_from(fields)
        data = {k: v for k, v in fields.items() if k not in ("latitude", "longitude")}
        if point is not None:
            data["location"] = point

        model.objects.create(facility_type=facility_type, **data)
