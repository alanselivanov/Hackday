import type { EnrichedHydroFacility } from '@/entities/facility/model/types';
import { PILOT_MAP_BOUNDS } from '@/shared/config/constants';
import type { LatLngBoundsExpression } from 'leaflet';

/** Границы по точкам объектов с небольшим отступом; иначе — пилотный bbox. */
export function getViewBounds(
  facilities: EnrichedHydroFacility[],
): LatLngBoundsExpression {
  if (facilities.length === 0) {
    return PILOT_MAP_BOUNDS;
  }

  let minLat = Infinity;
  let maxLat = -Infinity;
  let minLng = Infinity;
  let maxLng = -Infinity;

  for (const facility of facilities) {
    minLat = Math.min(minLat, facility.location.lat);
    maxLat = Math.max(maxLat, facility.location.lat);
    minLng = Math.min(minLng, facility.location.lng);
    maxLng = Math.max(maxLng, facility.location.lng);
  }

  const latPad = Math.max(0.04, (maxLat - minLat) * 0.15);
  const lngPad = Math.max(0.06, (maxLng - minLng) * 0.15);

  return [
    [minLat - latPad, minLng - lngPad],
    [maxLat + latPad, maxLng + lngPad],
  ];
}
