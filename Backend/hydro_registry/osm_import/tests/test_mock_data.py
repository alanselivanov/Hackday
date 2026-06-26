from django.test import TestCase

from osm_import.services.mock_data import MockDataGenerator
from osm_import.services.normalizer import NormalizedOSMObject


class MockDataGeneratorTests(TestCase):
    def _make_obj(self, facility_type="canal", osm_id=42):
        return NormalizedOSMObject(
            source="osm",
            osm_type="way",
            osm_id=osm_id,
            name="Test",
            latitude=43.0,
            longitude=69.0,
            tags={"waterway": "canal", "capacity": "10"},
            raw_geometry=[(69.0, 43.0), (69.5, 43.5)],
            facility_type=facility_type,
            confidence_score=1.0,
        )

    def test_deterministic_generation(self):
        obj = self._make_obj()
        gen = MockDataGenerator()
        first = gen.generate(obj)
        second = gen.generate(obj)
        self.assertEqual(first.base_fields["wear_percentage"], second.base_fields["wear_percentage"])
        self.assertEqual(first.type_fields["capacity"], second.type_fields["capacity"])

    def test_canal_fields_generated(self):
        result = MockDataGenerator().generate(self._make_obj("canal"))
        self.assertIn("capacity", result.type_fields)
        self.assertIn("total_length", result.type_fields)
        self.assertGreater(len(result.generated_fields), 0)

    def test_sluice_fields_generated(self):
        result = MockDataGenerator().generate(self._make_obj("sluice", 10))
        self.assertIn("gates_count", result.type_fields)
        self.assertIn("max_discharge", result.type_fields)

    def test_pumping_fields_generated(self):
        result = MockDataGenerator().generate(self._make_obj("pumping", 11))
        self.assertIn("installed_power", result.type_fields)
        self.assertIn("current_consumption", result.type_fields)

    def test_dam_fields_generated(self):
        result = MockDataGenerator().generate(self._make_obj("dam_dyke", 12))
        self.assertIn("crest_length", result.type_fields)
        self.assertIn("reservoir_volume", result.type_fields)

    def test_post_fields_generated(self):
        obj = self._make_obj("post", 14)
        obj.tags = {
            "monitoring:water_level": "yes",
            "recording:automated": "yes",
            "ref": "HP-42",
        }
        result = MockDataGenerator().generate(obj)
        self.assertEqual(result.type_fields["post_type"], "Автоматический")
        self.assertEqual(result.type_fields["equipment_installed"], "HP-42")
        self.assertIn("current_water_level", result.type_fields)
        self.assertIsNotNone(result.type_fields["last_telemetry_at"])

    def test_uses_osm_capacity_tag(self):
        result = MockDataGenerator().generate(self._make_obj("canal", 13))
        self.assertEqual(result.type_fields["capacity"], 10.0)
