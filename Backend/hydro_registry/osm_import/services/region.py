"""
Конфигурация территории импорта и порогов сопоставления.
Территория задаётся в коде (bbox) согласно плану MVP.
"""


class RegionConfig:
    """Заранее определённая территория импорта (Южный Казахстан, орошение)."""

    # south, west, north, east
    SOUTH = 51.80
    WEST = 74.80
    NORTH = 53.30
    EAST = 77.60

    @classmethod
    def bbox_string(cls) -> str:
        return f"{cls.SOUTH},{cls.WEST},{cls.NORTH},{cls.EAST}"


class ImportMatcherConfig:
    """Пороговые значения для FacilityMatcher."""

    STRONG_DISTANCE_METERS = 30
    POSSIBLE_DISTANCE_METERS = 100
    EXISTING_SCORE_THRESHOLD = 0.5
    NAME_FUZZY_THRESHOLD = 0.85

    DISTANCE_STRONG_SCORE = 0.4
    DISTANCE_POSSIBLE_SCORE = 0.2
    NAME_EXACT_SCORE = 0.3
    NAME_FUZZY_SCORE = 0.2
    TAG_MATCH_SCORE = 0.1
    TAG_MATCH_MAX = 0.3


class OverpassConfig:
    """Настройки Overpass API."""

    DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"
    TIMEOUT_SECONDS = 120
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 5
