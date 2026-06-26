from unittest.mock import patch

from django.contrib.gis.geos import Point
from django.test import TestCase

from analytics.models import FacilityAnalytics
from infrastructure.models import Canal
from monitoring.models import InspectionLog
from osm_import.models import OSMImportRecord
from osm_import.services.importer import FacilityImporter


SAMPLE_OVERPASS_RESPONSE = {
    "elements": [
        {
            "type": "node",
            "id": 1001,
            "lat": 43.25,
            "lon": 69.25,
            "tags": {"waterway": "canal", "name": "Import Canal"},
        },
        {
            "type": "node",
            "id": 1002,
            "lat": 43.26,
            "lon": 69.26,
            "tags": {"man_made": "pumping_station", "name": "Import Pump"},
        },
    ]
}


class FacilityImporterTests(TestCase):
    @patch("osm_import.services.client.OSMClient.fetch_facilities")
    def test_full_import_creates_facilities(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_OVERPASS_RESPONSE

        stats = FacilityImporter().run()

        self.assertEqual(stats.found, 2)
        self.assertEqual(stats.created, 2)
        self.assertEqual(stats.existing, 0)
        self.assertEqual(Canal.objects.count(), 1)
        self.assertEqual(OSMImportRecord.objects.count(), 2)
        self.assertEqual(FacilityAnalytics.objects.count(), 2)
        self.assertEqual(InspectionLog.objects.count(), 2)

    @patch("osm_import.services.client.OSMClient.fetch_facilities")
    def test_reimport_no_duplicates(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_OVERPASS_RESPONSE

        importer = FacilityImporter()
        first_stats = importer.run()
        second_stats = importer.run()

        self.assertEqual(first_stats.created, 2)
        self.assertEqual(second_stats.created, 0)
        self.assertEqual(second_stats.existing, 2)
        self.assertEqual(Canal.objects.count(), 1)

    @patch("osm_import.services.client.OSMClient.fetch_facilities")
    def test_existing_facility_linked_on_reimport(self, mock_fetch):
        mock_fetch.return_value = {
            "elements": [
                {
                    "type": "node",
                    "id": 2001,
                    "lat": 43.3,
                    "lon": 69.3,
                    "tags": {"waterway": "canal", "name": "Manual Canal"},
                }
            ]
        }

        Canal.objects.create(
            facility_type="canal",
            name="Manual Canal",
            water_source="River",
            district="Test",
            location=Point(69.3, 43.3, srid=4326),
        )

        stats = FacilityImporter().run()
        self.assertEqual(stats.created, 0)
        self.assertEqual(stats.existing, 1)
        self.assertEqual(Canal.objects.count(), 1)

        record = OSMImportRecord.objects.get(osm_id=2001)
        self.assertEqual(record.facility_type, "canal")

    @patch("osm_import.services.client.OSMClient.fetch_facilities")
    def test_overpass_error_handled(self, mock_fetch):
        mock_fetch.side_effect = RuntimeError("Overpass down")

        stats = FacilityImporter().run()
        self.assertEqual(stats.errors, 1)
        self.assertEqual(stats.created, 0)
