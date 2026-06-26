import random

from core.models import BaseHydroFacility


def ensure_calculation_inputs(facility: BaseHydroFacility) -> list[str]:
    """Заполнить недостающие входы алгоритма осмотра, не перетирая реальные данные."""
    updated_fields: list[str] = []
    rng = random.Random(
        f"{facility.pk}:{facility.facility_type}:{facility.name}:{facility.water_source}"
    )

    if facility.safety_class is None:
        facility.safety_class = _generate_safety_class(facility.facility_type, rng)
        updated_fields.append("safety_class")

    if facility.design_service_life is None and facility.safety_class is not None:
        facility.design_service_life = 100 if facility.safety_class in (1, 2) else 50
        updated_fields.append("design_service_life")

    if updated_fields:
        facility.save(update_fields=updated_fields)

    return updated_fields


def _generate_safety_class(facility_type: str | None, rng: random.Random) -> int:
    if facility_type in ("dam_dyke", "pumping"):
        return rng.choice([1, 2])
    if facility_type in ("sluice", "intake"):
        return rng.choice([2, 3])
    return rng.choice([3, 4])
