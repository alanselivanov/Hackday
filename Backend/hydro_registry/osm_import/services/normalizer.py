from dataclasses import dataclass, field
from typing import Any


@dataclass
class NormalizedOSMObject:
    """Единый внутренний формат OSM-объекта после нормализации."""

    source: str
    osm_type: str
    osm_id: int
    name: str
    latitude: float
    longitude: float
    tags: dict[str, str]
    raw_geometry: list[tuple[float, float]]
    facility_type: str | None = None
    confidence_score: float = 0.0


class OSMObjectNormalizer:
    """Перевод сырого Overpass JSON во внутренний формат."""

    def normalize_all(self, overpass_response: dict) -> list[NormalizedOSMObject]:
        elements = overpass_response.get("elements", [])
        nodes = {
            el["id"]: (el["lon"], el["lat"])
            for el in elements
            if el.get("type") == "node" and "lat" in el and "lon" in el
        }

        results: list[NormalizedOSMObject] = []
        seen: set[tuple[str, int]] = set()

        for element in elements:
            osm_type = element.get("type")
            if osm_type not in ("node", "way", "relation"):
                continue
            osm_id = element.get("id")
            if osm_id is None:
                continue

            key = (osm_type, osm_id)
            if key in seen:
                continue
            seen.add(key)

            tags = element.get("tags", {})
            geometry = self._extract_geometry(element, nodes)
            if not geometry:
                continue

            longitude, latitude = self._centroid(geometry)
            name = self._extract_name(tags, osm_type, osm_id)

            results.append(
                NormalizedOSMObject(
                    source="osm",
                    osm_type=osm_type,
                    osm_id=osm_id,
                    name=name,
                    latitude=latitude,
                    longitude=longitude,
                    tags=tags,
                    raw_geometry=geometry,
                )
            )

        return results

    def _extract_geometry(
        self,
        element: dict[str, Any],
        nodes: dict[int, tuple[float, float]],
    ) -> list[tuple[float, float]]:
        osm_type = element.get("type")

        if osm_type == "node" and "lat" in element and "lon" in element:
            return [(element["lon"], element["lat"])]

        if osm_type == "way":
            coords = []
            if "geometry" in element:
                for point in element["geometry"]:
                    coords.append((point["lon"], point["lat"]))
            elif "nodes" in element:
                for node_id in element["nodes"]:
                    if node_id in nodes:
                        coords.append(nodes[node_id])
            return coords

        if osm_type == "relation":
            coords = []
            for member in element.get("members", []):
                if member.get("type") == "node" and member.get("lat") and member.get("lon"):
                    coords.append((member["lon"], member["lat"]))
                elif member.get("type") == "way" and "geometry" in member:
                    for point in member["geometry"]:
                        coords.append((point["lon"], point["lat"]))
            return coords

        return []

    def _centroid(self, geometry: list[tuple[float, float]]) -> tuple[float, float]:
        if len(geometry) == 1:
            return geometry[0]
        lon_sum = sum(p[0] for p in geometry)
        lat_sum = sum(p[1] for p in geometry)
        count = len(geometry)
        return lon_sum / count, lat_sum / count

    def _extract_name(self, tags: dict[str, str], osm_type: str, osm_id: int) -> str:
        for key in ("name", "name:ru", "name:en", "ref"):
            if tags.get(key):
                return tags[key]
        return f"OSM {osm_type} {osm_id}"

    @staticmethod
    def compute_length_km(geometry: list[tuple[float, float]]) -> float | None:
        """Приблизительная длина линии в км (для каналов, дамб)."""
        if len(geometry) < 2:
            return None

        from math import asin, cos, radians, sin, sqrt

        total_m = 0.0
        for i in range(len(geometry) - 1):
            lon1, lat1 = geometry[i]
            lon2, lat2 = geometry[i + 1]
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            total_m += 2 * asin(sqrt(a)) * 6371000

        return round(total_m / 1000, 3)
