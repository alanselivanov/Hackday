from django.core.exceptions import ObjectDoesNotExist

from infrastructure.models import Canal, DamsAndDykes, PumpingStation, Sluice, WaterIntake
from monitoring.models import HydroPost


def serialize_location(point):
    if not point:
        return None
    return {"type": "Point", "coordinates": [point.x, point.y]}


def serialize_analytics(facility):
    try:
        analytics = facility.analytics
    except ObjectDoesNotExist:
        return None

    next_inspection_date = analytics.next_inspection_date
    status_changed_at = analytics.status_changed_at
    updated_at = analytics.updated_at

    return {
        "repair_status": analytics.repair_status,
        "repair_status_display": analytics.get_repair_status_display(),
        "inspection_interval_days": analytics.inspection_interval_days,
        "next_inspection_date": (
            next_inspection_date.isoformat() if next_inspection_date else None
        ),
        "calculated_importance": analytics.calculated_importance,
        "calculated_importance_display": analytics.get_calculated_importance_display(),
        "condition_score": analytics.condition_score,
        "repair_status_reason": analytics.repair_status_reason,
        "requires_verification": analytics.requires_verification,
        "last_inspection_id": (
            analytics.last_inspection_id if analytics.last_inspection_id else None
        ),
        "status_changed_at": status_changed_at.isoformat() if status_changed_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def serialize_facility(facility):
    data = {
        "id": facility.pk,
        "facility_type": facility.facility_type,
        "facility_type_display": facility.get_facility_type_display(),
        "name": facility.name,
        "water_source": facility.water_source,
        "district": facility.district,
        "rural_district": facility.rural_district,
        "cadastral_number": facility.cadastral_number,
        "state_act": facility.state_act,
        "location": serialize_location(facility.location),
        "year_built": facility.year_built,
        "year_balanced": facility.year_balanced,
        "wear_percentage": facility.wear_percentage,
        "technical_condition": facility.technical_condition,
        "efficiency_project": facility.efficiency_project,
        "efficiency_fact": facility.efficiency_fact,
        "is_emergency_prone": facility.is_emergency_prone,
        "analytics": serialize_analytics(facility),
        "specific": _serialize_specific(facility),
    }
    return data


def _serialize_specific(facility):
    if isinstance(facility, Canal):
        return {
            "capacity": facility.capacity,
            "total_length": facility.total_length,
            "earth_length": facility.earth_length,
            "lined_length": facility.lined_length,
            "area_regular": facility.area_regular,
            "area_liman": facility.area_liman,
            "area_flooded": facility.area_flooded,
            "bottom_width": facility.bottom_width,
            "top_width": facility.top_width,
            "depth": facility.depth,
        }
    if isinstance(facility, Sluice):
        return {
            "gates_count": facility.gates_count,
            "gate_type": facility.gate_type,
            "drive_type": facility.drive_type,
            "max_discharge": facility.max_discharge,
        }
    if isinstance(facility, WaterIntake):
        return {
            "intake_type": facility.intake_type,
            "is_gravity": facility.is_gravity,
            "fish_protection": facility.fish_protection,
            "max_volume_clean": facility.max_volume_clean,
        }
    if isinstance(facility, PumpingStation):
        return {
            "pumps_count": facility.pumps_count,
            "installed_power": facility.installed_power,
            "current_consumption": facility.current_consumption,
            "head_pressure": facility.head_pressure,
        }
    if isinstance(facility, DamsAndDykes):
        return {
            "material": facility.material,
            "crest_length": facility.crest_length,
            "max_height": facility.max_height,
            "reservoir_volume": facility.reservoir_volume,
            "is_declared_dangerous": facility.is_declared_dangerous,
        }
    if isinstance(facility, HydroPost):
        return {
            "post_type": facility.post_type,
            "equipment_installed": facility.equipment_installed,
            "current_water_level": facility.current_water_level,
            "critical_water_level": facility.critical_water_level,
            "last_telemetry_at": (
                facility.last_telemetry_at.isoformat() if facility.last_telemetry_at else None
            ),
        }
    return {}
