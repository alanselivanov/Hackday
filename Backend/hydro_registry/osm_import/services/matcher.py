import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum
from math import asin, cos, radians, sin, sqrt
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point, Polygon

from core.models import BaseHydroFacility
from infrastructure.models import Canal, DamsAndDykes, PumpingStation, Sluice, WaterIntake
from monitoring.models import HydroPost
from osm_import.models import OSMImportRecord
from osm_import.services.normalizer import NormalizedOSMObject
from osm_import.services.region import ImportMatcherConfig

FACILITY_MODEL_MAP = {
    "canal": Canal,
    "post": HydroPost,
    "sluice": Sluice,
    "intake": WaterIntake,
    "pumping": PumpingStation,
    "dam_dyke": DamsAndDykes,
}

COMPARE_TAGS = ("waterway", "man_made", "operator", "usage", "material", "length", "capacity", "ref")


class MatchResult(Enum):
    EXISTING = "EXISTING"
    NEW = "NEW"


@dataclass
class MatchOutcome:
    result: MatchResult
    score: float
    matched_facility: BaseHydroFacility | None = None
    import_record: OSMImportRecord | None = None


class FacilityMatcher:
    """Сопоставление OSM-объекта с существующими записами в БД."""

    def __init__(self, config: ImportMatcherConfig | None = None):
        self.config = config or ImportMatcherConfig()

    def match(self, obj: NormalizedOSMObject) -> MatchOutcome:
        import_record = OSMImportRecord.objects.filter(
            source=obj.source,
            osm_type=obj.osm_type,
            osm_id=obj.osm_id,
        ).select_related("content_type").first()

        if import_record:
            facility = import_record.facility
            return MatchOutcome(
                result=MatchResult.EXISTING,
                score=1.0,
                matched_facility=facility,
                import_record=import_record,
            )

        model_class = FACILITY_MODEL_MAP.get(obj.facility_type)
        if not model_class:
            return MatchOutcome(result=MatchResult.NEW, score=0.0)

        point = Point(obj.longitude, obj.latitude, srid=4326)
        candidates = self._get_spatial_candidates(model_class, obj)

        best_facility = None
        best_score = 0.0

        for candidate in candidates:
            score = self._compute_score(obj, candidate, point)
            if score > best_score:
                best_score = score
                best_facility = candidate

        if best_facility and best_score >= self.config.EXISTING_SCORE_THRESHOLD:
            return MatchOutcome(
                result=MatchResult.EXISTING,
                score=best_score,
                matched_facility=best_facility,
            )

        return MatchOutcome(result=MatchResult.NEW, score=best_score)

    def _get_spatial_candidates(self, model_class, obj: NormalizedOSMObject):
        meters = self.config.POSSIBLE_DISTANCE_METERS
        lat_delta = meters / 111320.0
        lon_delta = meters / (111320.0 * max(cos(radians(obj.latitude)), 0.01))

        bbox = Polygon.from_bbox(
            (
                obj.longitude - lon_delta,
                obj.latitude - lat_delta,
                obj.longitude + lon_delta,
                obj.latitude + lat_delta,
            )
        )
        bbox.srid = 4326

        return model_class.objects.filter(
            facility_type=obj.facility_type,
            location__within=bbox,
        )

    def _compute_score(
        self,
        obj: NormalizedOSMObject,
        candidate: BaseHydroFacility,
        point: Point,
    ) -> float:
        score = 0.0

        if candidate.location:
            distance_m = self._haversine_meters(
                obj.longitude,
                obj.latitude,
                candidate.location.x,
                candidate.location.y,
            )
            if distance_m <= self.config.STRONG_DISTANCE_METERS:
                score += self.config.DISTANCE_STRONG_SCORE
            elif distance_m <= self.config.POSSIBLE_DISTANCE_METERS:
                score += self.config.DISTANCE_POSSIBLE_SCORE

        name_score = self._name_similarity(obj.name, candidate.name)
        if name_score == 1.0:
            score += self.config.NAME_EXACT_SCORE
        elif name_score >= self.config.NAME_FUZZY_THRESHOLD:
            score += self.config.NAME_FUZZY_SCORE

        tag_matches = self._count_tag_matches(obj.tags, candidate)
        score += min(
            tag_matches * self.config.TAG_MATCH_SCORE,
            self.config.TAG_MATCH_MAX,
        )

        return round(score, 3)

    def _name_similarity(self, name_a: str, name_b: str) -> float:
        norm_a = self._normalize_name(name_a)
        norm_b = self._normalize_name(name_b)
        if not norm_a or not norm_b:
            return 0.0
        if norm_a == norm_b:
            return 1.0
        return SequenceMatcher(None, norm_a, norm_b).ratio()

    def _normalize_name(self, name: str) -> str:
        name = name.lower().strip()
        name = re.sub(r"['\"«»]", "", name)
        name = re.sub(r"\s+", " ", name)
        replacements = {
            "канал": "canal",
            "шлюз": "sluice",
            "водозабор": "intake",
            "насосная": "pumping",
            "плотина": "dam",
            "дамба": "dyke",
            "гидропост": "post",
            "пегель": "post",
        }
        for ru, en in replacements.items():
            name = name.replace(ru, en)
        return name

    def _count_tag_matches(self, tags: dict[str, str], candidate: BaseHydroFacility) -> int:
        matches = 0
        candidate_text = f"{candidate.name} {candidate.water_source} {candidate.technical_condition or ''}".lower()
        for key in COMPARE_TAGS:
            value = tags.get(key)
            if value and value.lower() in candidate_text:
                matches += 1
        return matches

    @staticmethod
    def _haversine_meters(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return 2 * asin(sqrt(a)) * 6371000

    @staticmethod
    def get_model_for_type(facility_type: str):
        return FACILITY_MODEL_MAP.get(facility_type)

    @staticmethod
    def get_content_type_for_facility(facility: BaseHydroFacility) -> ContentType:
        return ContentType.objects.get_for_model(facility)
