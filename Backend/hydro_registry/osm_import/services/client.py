import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request

from osm_import.services.region import OverpassConfig, RegionConfig

logger = logging.getLogger(__name__)

# OSM-теги для поиска по типам (согласно плану)
FACILITY_TAG_QUERIES = {
    "canal": [
        ("waterway", "canal"),
        ("waterway", "ditch"),
        ("waterway", "drain"),
    ],
    "sluice": [
        ("waterway", "lock_gate"),
        ("waterway", "sluice"),
        ("man_made", "sluice_gate"),
    ],
    "intake": [
        ("man_made", "water_works"),
        ("waterway", "intake"),
        ("water", "water_intake"),
    ],
    "pumping": [
        ("man_made", "pumping_station"),
    ],
    "dam_dyke": [
        ("waterway", "dam"),
        ("barrier", "dam"),
        ("man_made", "dyke"),
        ("embankment", "yes"),
    ],
    "post": [
        ("monitoring:water_level", "yes"),
        ("monitoring:tide_gauge", "yes"),
        ("building", "gauge_house"),
    ],
}

# Дополнительные тег-фильтры (без конкретного значения ключа)
EXTRA_TAG_FILTERS = {
    "canal": [("usage", "irrigation")],
    "sluice": [("lock", "yes")],
    "pumping": [
        ("pumping_station", "yes"),
        ("pump", "yes"),
        ("utility", "water"),
        ("substance", "water"),
    ],
    "post": [
        ("man_made", "monitoring_station"),
    ],
}


class OSMClient:
    """Клиент Overpass API для получения гидротехнических объектов."""

    def __init__(
        self,
        endpoint: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ):
        self.endpoint = endpoint or OverpassConfig.DEFAULT_ENDPOINT
        self.timeout = timeout or OverpassConfig.TIMEOUT_SECONDS
        self.max_retries = max_retries or OverpassConfig.MAX_RETRIES

    def fetch_facilities(self, region: RegionConfig | None = None) -> dict:
        region = region or RegionConfig()
        query = self._build_query(region)
        return self._execute_query(query)

    def _build_query(self, region: RegionConfig) -> str:
        bbox = region.bbox_string()
        selectors = []

        for facility_type, tag_pairs in FACILITY_TAG_QUERIES.items():
            for key, value in tag_pairs:
                for osm_type in ("node", "way", "relation"):
                    selectors.append(f'{osm_type}["{key}"="{value}"]({bbox});')

        for facility_type, tag_pairs in EXTRA_TAG_FILTERS.items():
            for key, value in tag_pairs:
                for osm_type in ("node", "way", "relation"):
                    selectors.append(f'{osm_type}["{key}"="{value}"]({bbox});')

        body = "\n  ".join(selectors)
        return f"""
[out:json][timeout:{self.timeout}];
(
  {body}
);
out body;
>;
out skel qt;
"""

    def _execute_query(self, query: str) -> dict:
        payload = urllib.parse.urlencode({"data": query.strip()}).encode("utf-8")
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                request = urllib.request.Request(
                    self.endpoint,
                    data=payload,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                        "User-Agent": "hydro_registry-osm-import/1.0",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                last_error = exc
                logger.warning(
                    "Overpass API ошибка (попытка %s/%s): %s",
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(OverpassConfig.RETRY_DELAY_SECONDS)

        raise RuntimeError(f"Overpass API недоступен после {self.max_retries} попыток: {last_error}")
