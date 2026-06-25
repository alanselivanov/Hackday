"""Запись сооружений через Django ORM. Единственное место, зависящее от GeoDjango.

Собирает координаты из псевдополей latitude/longitude в location (PointField).
На срезе #01 поддержан только канал; остальные типы добавляются в #07.
"""

from __future__ import annotations

from django.contrib.gis.geos import Point

from infrastructure.models import Canal

from ...application.ports import FacilityRepository

_MODEL_BY_TYPE = {
    "canal": Canal,
}


class DjangoFacilityRepository(FacilityRepository):
    def create(self, *, facility_type: str, fields: dict) -> None:
        model = _MODEL_BY_TYPE.get(facility_type)
        if model is None:
            raise ValueError(f"Неподдерживаемый тип сооружения: {facility_type}")

        data = dict(fields)
        latitude = data.pop("latitude", None)
        longitude = data.pop("longitude", None)
        if latitude is not None and longitude is not None:
            data["location"] = Point(float(longitude), float(latitude), srid=4326)

        model.objects.create(facility_type=facility_type, **data)
