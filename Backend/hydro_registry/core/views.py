from django.http import JsonResponse
from django.views import View

from core.models import BaseHydroFacility
from core.serializers import serialize_facility


class FacilityListAPIView(View):
    """GET /api/facilities/ — список всех гидросооружений с фильтром по типу."""

    VALID_TYPES = {choice[0] for choice in BaseHydroFacility.FACILITY_TYPES}

    def get(self, request):
        queryset = BaseHydroFacility.objects.select_related("analytics").order_by("id")

        raw_types = request.GET.get("facility_type", "")
        if raw_types:
            requested = [value.strip() for value in raw_types.split(",") if value.strip()]
            invalid = [value for value in requested if value not in self.VALID_TYPES]
            if invalid:
                return JsonResponse(
                    {
                        "error": "Неверный facility_type",
                        "invalid_values": invalid,
                        "allowed_values": sorted(self.VALID_TYPES),
                    },
                    status=400,
                )
            queryset = queryset.filter(facility_type__in=requested)

        facilities = [serialize_facility(facility) for facility in queryset]
        return JsonResponse(
            {
                "count": len(facilities),
                "filters": {
                    "facility_type": raw_types or None,
                },
                "available_types": [
                    {"value": value, "label": label}
                    for value, label in BaseHydroFacility.FACILITY_TYPES
                ],
                "results": facilities,
            }
        )
