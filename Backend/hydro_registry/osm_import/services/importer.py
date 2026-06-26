import logging
from dataclasses import dataclass, field

from django.contrib.gis.geos import Point
from django.db import transaction
from django.utils import timezone

from analytics.calculation_inputs import ensure_calculation_inputs
from analytics.services import recalculate_status
from core.models import BaseHydroFacility
from inspection_service import run_for_facility
from osm_import.models import OSMImportRecord
from osm_import.services.classifier import FacilityClassifier
from osm_import.services.client import OSMClient
from osm_import.services.matcher import FacilityMatcher, MatchResult
from osm_import.services.mock_data import MockDataGenerator
from osm_import.services.normalizer import OSMObjectNormalizer
from osm_import.services.region import RegionConfig

logger = logging.getLogger(__name__)


@dataclass
class ImportStatistics:
    found: int = 0
    created: int = 0
    existing: int = 0
    skipped_classification: int = 0
    errors: int = 0
    error_details: list[str] = field(default_factory=list)


class FacilityImporter:
    """Оркестратор полного процесса импорта из OpenStreetMap."""

    def __init__(
        self,
        client: OSMClient | None = None,
        normalizer: OSMObjectNormalizer | None = None,
        classifier: FacilityClassifier | None = None,
        matcher: FacilityMatcher | None = None,
        mock_generator: MockDataGenerator | None = None,
        region: RegionConfig | None = None,
    ):
        self.client = client or OSMClient()
        self.normalizer = normalizer or OSMObjectNormalizer()
        self.classifier = classifier or FacilityClassifier()
        self.matcher = matcher or FacilityMatcher()
        self.mock_generator = mock_generator or MockDataGenerator()
        self.region = region or RegionConfig()

    def run(self) -> ImportStatistics:
        stats = ImportStatistics()

        try:
            overpass_data = self.client.fetch_facilities(self.region)
        except Exception as exc:
            stats.errors += 1
            stats.error_details.append(f"Overpass API: {exc}")
            logger.exception("Не удалось получить данные из Overpass API")
            return stats

        normalized_objects = self.normalizer.normalize_all(overpass_data)
        stats.found = len(normalized_objects)

        for obj in normalized_objects:
            try:
                self._process_object(obj, stats)
            except Exception as exc:
                stats.errors += 1
                message = f"OSM {obj.osm_type}/{obj.osm_id}: {exc}"
                stats.error_details.append(message)
                logger.exception(message)

        return stats

    def _process_object(self, obj, stats: ImportStatistics):
        classified = self.classifier.classify(obj)
        if classified is None:
            stats.skipped_classification += 1
            logger.info(
                "Пропуск OSM %s/%s: не удалось классифицировать",
                obj.osm_type,
                obj.osm_id,
            )
            return

        outcome = self.matcher.match(classified)

        if outcome.result == MatchResult.EXISTING:
            stats.existing += 1
            self._handle_existing(classified, outcome)
            return

        self._create_facility(classified, stats)

    def _handle_existing(self, obj, outcome):
        now = timezone.now()

        if outcome.import_record:
            outcome.import_record.last_seen_at = now
            outcome.import_record.raw_tags = obj.tags
            outcome.import_record.save(update_fields=["last_seen_at", "raw_tags"])
            if outcome.import_record.facility:
                self._recalculate_analytics(outcome.import_record.facility)
            return

        if outcome.matched_facility:
            content_type = FacilityMatcher.get_content_type_for_facility(outcome.matched_facility)
            OSMImportRecord.objects.update_or_create(
                source=obj.source,
                osm_type=obj.osm_type,
                osm_id=obj.osm_id,
                defaults={
                    "facility_type": obj.facility_type,
                    "content_type": content_type,
                    "object_id": outcome.matched_facility.pk,
                    "raw_tags": obj.tags,
                    "last_seen_at": now,
                },
            )
            self._recalculate_analytics(outcome.matched_facility)

    @transaction.atomic
    def _create_facility(self, obj, stats: ImportStatistics):
        model_class = FacilityMatcher.get_model_for_type(obj.facility_type)
        if not model_class:
            stats.errors += 1
            stats.error_details.append(
                f"OSM {obj.osm_type}/{obj.osm_id}: неизвестный тип {obj.facility_type}"
            )
            return

        mock_result = self.mock_generator.generate(obj)
        point = Point(obj.longitude, obj.latitude, srid=4326)

        facility_data = dict(mock_result.base_fields)
        facility_data["location"] = point
        facility_data.update(mock_result.type_fields)

        facility = model_class.objects.create(**facility_data)
        self._recalculate_analytics(facility)

        content_type = FacilityMatcher.get_content_type_for_facility(facility)
        OSMImportRecord.objects.create(
            source=obj.source,
            osm_type=obj.osm_type,
            osm_id=obj.osm_id,
            facility_type=obj.facility_type,
            content_type=content_type,
            object_id=facility.pk,
            raw_tags=obj.tags,
        )

        stats.created += 1
        logger.info(
            "Создан объект %s (%s) из OSM %s/%s",
            facility.name,
            obj.facility_type,
            obj.osm_type,
            obj.osm_id,
        )

    def _recalculate_analytics(self, facility: BaseHydroFacility):
        ensure_calculation_inputs(facility)
        run_for_facility(facility)
        analytics = facility.analytics
        analytics.calculated_importance = self._calculate_importance(facility)
        analytics.save(update_fields=["calculated_importance", "updated_at"])
        recalculate_status(analytics)

    def _calculate_importance(self, facility: BaseHydroFacility) -> str:
        if facility.facility_type in ("dam_dyke", "pumping"):
            return "high"
        if facility.facility_type in ("sluice", "intake"):
            return "medium"
        if facility.is_emergency_prone:
            return "high"
        return "low"
