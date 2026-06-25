from osm_import.services.client import FACILITY_TAG_QUERIES, EXTRA_TAG_FILTERS
from osm_import.services.normalizer import NormalizedOSMObject


class FacilityClassifier:
    """Определение локального типа гидротехнического сооружения по OSM-тегам."""

    MIN_CONFIDENCE = 0.5

    def classify(self, obj: NormalizedOSMObject) -> NormalizedOSMObject | None:
        tags = obj.tags
        scores: dict[str, float] = {}

        for facility_type, tag_pairs in FACILITY_TAG_QUERIES.items():
            score = self._score_tag_pairs(tags, tag_pairs)
            if score > 0:
                scores[facility_type] = max(scores.get(facility_type, 0), score)

        for facility_type, tag_pairs in EXTRA_TAG_FILTERS.items():
            score = self._score_tag_pairs(tags, tag_pairs)
            if score > 0:
                scores[facility_type] = max(scores.get(facility_type, 0), score * 0.8)

        if not scores:
            return None

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        if best_type == "intake" and best_score < 1.0:
            return None

        if best_type == "post" and best_score < 1.0:
            return None

        if best_score < self.MIN_CONFIDENCE:
            return None

        obj.facility_type = best_type
        obj.confidence_score = round(best_score, 2)
        return obj

    def _score_tag_pairs(self, tags: dict[str, str], tag_pairs: list[tuple[str, str]]) -> float:
        for key, value in tag_pairs:
            if tags.get(key) == value:
                return 1.0
        return 0.0
