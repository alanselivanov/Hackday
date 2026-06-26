from django.contrib.gis.geos import Point
from django.test import TestCase

from infrastructure.models import Canal
from osm_import.models import OSMImportRecord
from osm_import.services.matcher import FacilityMatcher, MatchResult
from osm_import.services.normalizer import NormalizedOSMObject


class FacilityMatcherTests(TestCase):
    def _make_obj(self, osm_id=100, facility_type="canal", name="Test Canal", lon=69.0, lat=43.0):
        return NormalizedOSMObject(
            source="osm",
            osm_type="way",
            osm_id=osm_id,
            name=name,
            latitude=lat,
            longitude=lon,
            tags={"waterway": "canal"},
            raw_geometry=[(lon, lat)],
            facility_type=facility_type,
            confidence_score=1.0,
        )

    def test_existing_by_osm_id(self):
        canal = Canal.objects.create(
            facility_type="canal",
            name="Existing Canal",
            water_source="River",
            district="Test",
            location=Point(69.0, 43.0, srid=4326),
        )
        from django.contrib.contenttypes.models import ContentType

        OSMImportRecord.objects.create(
            source="osm",
            osm_type="way",
            osm_id=999,
            facility_type="canal",
            content_type=ContentType.objects.get_for_model(Canal),
            object_id=canal.pk,
            raw_tags={"waterway": "canal"},
        )

        obj = self._make_obj(osm_id=999)
        outcome = FacilityMatcher().match(obj)
        self.assertEqual(outcome.result, MatchResult.EXISTING)
        self.assertEqual(outcome.matched_facility.pk, canal.pk)

    def test_new_when_no_match(self):
        obj = self._make_obj(osm_id=200, lon=70.0, lat=44.0)
        outcome = FacilityMatcher().match(obj)
        self.assertEqual(outcome.result, MatchResult.NEW)

    def test_existing_by_spatial_and_name(self):
        Canal.objects.create(
            facility_type="canal",
            name="Main Canal",
            water_source="River",
            district="Test",
            location=Point(69.0001, 43.0001, srid=4326),
        )
        obj = self._make_obj(osm_id=300, name="Main Canal")
        outcome = FacilityMatcher().match(obj)
        self.assertEqual(outcome.result, MatchResult.EXISTING)
