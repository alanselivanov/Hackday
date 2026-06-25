import random
from dataclasses import dataclass, field

from django.utils import timezone

from osm_import.services.normalizer import NormalizedOSMObject, OSMObjectNormalizer


@dataclass
class MockGenerationResult:
    base_fields: dict
    type_fields: dict
    generated_fields: list[str] = field(default_factory=list)


class MockDataGenerator:
    """Детерминированная генерация mock-данных для отсутствующих характеристик."""

    GATE_TYPES = ["щитовой", "сегментный", "плоский"]
    DRIVE_TYPES = ["ручной", "механический", "электрический"]
    INTAKE_TYPES = ["Береговой", "русловой", "плавучий"]
    MATERIALS = ["Земляная", "бетонная", "каменно-набросная"]
    POST_TYPES = ["Автоматический", "Ручной"]
    EQUIPMENT_MODELS = [
        "HydroSense WL-200",
        "AquaGauge Pro",
        "RiverScan Echo-5",
        "LevelMaster RTU",
    ]

    def generate(self, obj: NormalizedOSMObject) -> MockGenerationResult:
        seed = f"{obj.osm_type}{obj.osm_id}{obj.facility_type}"
        rng = random.Random(seed)
        generated: list[str] = []

        base_fields = self._generate_base_fields(obj, rng, generated)
        type_fields = self._generate_type_fields(obj, rng, generated)

        return MockGenerationResult(
            base_fields=base_fields,
            type_fields=type_fields,
            generated_fields=generated,
        )

    def _generate_base_fields(
        self,
        obj: NormalizedOSMObject,
        rng: random.Random,
        generated: list[str],
    ) -> dict:
        tags = obj.tags
        fields = {
            "facility_type": obj.facility_type,
            "name": obj.name,
            "water_source": tags.get("waterway", tags.get("natural", "Не указан")),
            "district": tags.get("addr:district", "Импорт OSM"),
            "location": None,
            "wear_percentage": round(rng.uniform(5, 35), 1),
            "technical_condition": rng.choice(["удовлетворительное", "хорошее", "рабочее"]),
            "year_built": rng.randint(1960, 2015),
            "year_balanced": rng.randint(1965, 2020),
            "efficiency_project": round(rng.uniform(0.65, 0.92), 2),
            "efficiency_fact": round(rng.uniform(0.55, 0.88), 2),
            "is_emergency_prone": rng.random() < 0.1,
        }
        generated.extend(
            [
                "water_source",
                "district",
                "wear_percentage",
                "technical_condition",
                "year_built",
                "year_balanced",
                "efficiency_project",
                "efficiency_fact",
                "is_emergency_prone",
            ]
        )
        if tags.get("operator"):
            fields["water_source"] = tags["operator"]
        return fields

    def _generate_type_fields(
        self,
        obj: NormalizedOSMObject,
        rng: random.Random,
        generated: list[str],
    ) -> dict:
        facility_type = obj.facility_type
        tags = obj.tags
        length_km = OSMObjectNormalizer.compute_length_km(obj.raw_geometry)

        if facility_type == "canal":
            total_length = length_km or round(rng.uniform(0.5, 20), 2)
            earth = round(total_length * rng.uniform(0.4, 0.8), 2)
            lined = round(total_length - earth, 2)
            capacity = self._tag_float(tags, "capacity") or round(rng.uniform(2, 80), 2)
            area_regular = round(total_length * capacity * rng.uniform(8, 25), 1)
            fields = {
                "capacity": capacity,
                "total_length": total_length,
                "earth_length": earth,
                "lined_length": max(lined, 0),
                "area_regular": area_regular,
                "area_liman": round(area_regular * rng.uniform(0, 0.3), 1),
                "area_flooded": round(area_regular * rng.uniform(0, 0.2), 1),
                "bottom_width": round(rng.uniform(1, 12), 1),
                "top_width": round(rng.uniform(3, 30), 1),
                "depth": round(rng.uniform(1, 5), 1),
            }
            generated.extend(list(fields.keys()))
            return fields

        if facility_type == "sluice":
            fields = {
                "gates_count": rng.randint(1, 6),
                "gate_type": rng.choice(self.GATE_TYPES),
                "drive_type": rng.choice(self.DRIVE_TYPES),
                "max_discharge": self._tag_float(tags, "capacity") or round(rng.uniform(5, 150), 2),
            }
            generated.extend(list(fields.keys()))
            return fields

        if facility_type == "intake":
            is_gravity = tags.get("pump") != "yes"
            fields = {
                "intake_type": rng.choice(self.INTAKE_TYPES),
                "is_gravity": is_gravity,
                "fish_protection": rng.random() < 0.25,
                "max_volume_clean": round(rng.uniform(0.5, 50), 2),
            }
            generated.extend(list(fields.keys()))
            return fields

        if facility_type == "pumping":
            power = round(rng.uniform(15, 1000), 1)
            fields = {
                "pumps_count": rng.randint(1, 8),
                "installed_power": power,
                "current_consumption": round(power * rng.uniform(0.6, 0.95), 1),
                "head_pressure": round(rng.uniform(5, 80), 1),
            }
            generated.extend(list(fields.keys()))
            return fields

        if facility_type == "post":
            is_automated = tags.get("recording:automated") == "yes" or tags.get("recording:remote") == "yes"
            is_manual = tags.get("recording:manually") == "yes"
            if is_automated:
                post_type = "Автоматический"
            elif is_manual:
                post_type = "Ручной"
            else:
                post_type = rng.choice(self.POST_TYPES)
            current_level = round(rng.uniform(20, 350), 1)
            critical_level = round(current_level + rng.uniform(30, 120), 1)
            fields = {
                "post_type": post_type,
                "equipment_installed": tags.get("ref", rng.choice(self.EQUIPMENT_MODELS)),
                "current_water_level": current_level,
                "critical_water_level": critical_level,
                "last_telemetry_at": timezone.now() if post_type == "Автоматический" else None,
            }
            generated.extend(list(fields.keys()))
            return fields

        if facility_type == "dam_dyke":
            crest_length = None
            if length_km:
                crest_length = round(length_km * 1000, 1)
            else:
                crest_length = round(rng.uniform(50, 5000), 1)
            fields = {
                "material": tags.get("material", rng.choice(self.MATERIALS)),
                "crest_length": crest_length,
                "max_height": round(rng.uniform(2, 30), 1),
                "reservoir_volume": round(rng.uniform(0.1, 100), 2),
                "is_declared_dangerous": False,
            }
            generated.extend(list(fields.keys()))
            return fields

        return {}

    @staticmethod
    def _tag_float(tags: dict[str, str], key: str) -> float | None:
        value = tags.get(key)
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None
