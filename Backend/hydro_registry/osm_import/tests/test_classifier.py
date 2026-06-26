from django.test import TestCase

from osm_import.services.classifier import FacilityClassifier
from osm_import.services.normalizer import NormalizedOSMObject


class FacilityClassifierTests(TestCase):
    def test_classify_canal(self):
        obj = NormalizedOSMObject(
            source="osm",
            osm_type="way",
            osm_id=1,
            name="Test Canal",
            latitude=43.0,
            longitude=69.0,
            tags={"waterway": "canal"},
            raw_geometry=[(69.0, 43.0), (69.1, 43.1)],
        )
        result = FacilityClassifier().classify(obj)
        self.assertIsNotNone(result)
        self.assertEqual(result.facility_type, "canal")
        self.assertGreaterEqual(result.confidence_score, 0.5)

    def test_classify_sluice(self):
        obj = NormalizedOSMObject(
            source="osm",
            osm_type="node",
            osm_id=2,
            name="Test Sluice",
            latitude=43.0,
            longitude=69.0,
            tags={"waterway": "lock_gate"},
            raw_geometry=[(69.0, 43.0)],
        )
        result = FacilityClassifier().classify(obj)
        self.assertEqual(result.facility_type, "sluice")

    def test_classify_pumping_station(self):
        obj = NormalizedOSMObject(
            source="osm",
            osm_type="node",
            osm_id=3,
            name="Pump",
            latitude=43.0,
            longitude=69.0,
            tags={"man_made": "pumping_station"},
            raw_geometry=[(69.0, 43.0)],
        )
        result = FacilityClassifier().classify(obj)
        self.assertEqual(result.facility_type, "pumping")

    def test_classify_hydro_post(self):
        obj = NormalizedOSMObject(
            source="osm",
            osm_type="node",
            osm_id=6,
            name="River Gauge",
            latitude=43.0,
            longitude=69.0,
            tags={"monitoring:water_level": "yes", "man_made": "monitoring_station"},
            raw_geometry=[(69.0, 43.0)],
        )
        result = FacilityClassifier().classify(obj)
        self.assertEqual(result.facility_type, "post")

    def test_monitoring_station_without_water_tags_rejected(self):
        obj = NormalizedOSMObject(
            source="osm",
            osm_type="node",
            osm_id=7,
            name="Weather station",
            latitude=43.0,
            longitude=69.0,
            tags={"man_made": "monitoring_station", "monitoring:weather": "yes"},
            raw_geometry=[(69.0, 43.0)],
        )
        result = FacilityClassifier().classify(obj)
        self.assertIsNone(result)

    def test_ambiguous_intake_rejected(self):
        obj = NormalizedOSMObject(
            source="osm",
            osm_type="node",
            osm_id=4,
            name="Maybe intake",
            latitude=43.0,
            longitude=69.0,
            tags={"description": "possible water intake"},
            raw_geometry=[(69.0, 43.0)],
        )
        result = FacilityClassifier().classify(obj)
        self.assertIsNone(result)

    def test_unknown_tags_rejected(self):
        obj = NormalizedOSMObject(
            source="osm",
            osm_type="node",
            osm_id=5,
            name="Unknown",
            latitude=43.0,
            longitude=69.0,
            tags={"amenity": "cafe"},
            raw_geometry=[(69.0, 43.0)],
        )
        result = FacilityClassifier().classify(obj)
        self.assertIsNone(result)
