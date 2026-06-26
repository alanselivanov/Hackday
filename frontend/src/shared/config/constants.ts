import type { FacilityType, RepairStatus } from '@/entities/facility/model/types';

export const FACILITY_TYPE_LABELS: Record<FacilityType, string> = {
  canal: 'Канал',
  post: 'Гидропост',
  sluice: 'Шлюз',
  intake: 'Водозабор',
  pumping: 'Насосная станция',
  dam_dyke: 'Плотина / дамба',
};

export const REPAIR_STATUS_LABELS: Record<RepairStatus, string> = {
  normal: 'Норма',
  inspection_required: 'Требуется осмотр',
  repair_required: 'Требуется ремонт',
  critical: 'Критическое состояние',
};

export const REPAIR_STATUS_COLORS: Record<RepairStatus, string> = {
  normal: '#22c55e',
  inspection_required: '#eab308',
  repair_required: '#f97316',
  critical: '#ef4444',
};

export const PILOT_BBOX = {
  south: 51.8,
  west: 74.8,
  north: 53.3,
  east: 77.6,
};

/** Узкий пилотный участок реки Иртыш в заданном bbox, формат Leaflet: [lat, lng]. */
export const IRTYSH_PILOT_POLYLINE: [number, number][] = [
  [52.2, 74.86],
  [52.27, 75.08],
  [52.34, 75.32],
  [52.41, 75.58],
  [52.5, 75.88],
  [52.58, 76.18],
  [52.64, 76.46],
  [52.7, 76.78],
  [52.78, 77.08],
  [52.88, 77.34],
  [52.98, 77.56],
];

export const PILOT_MAP_CENTER: [number, number] = [52.55, 76.2];

export const PILOT_MAP_BOUNDS: [[number, number], [number, number]] = [
  [PILOT_BBOX.south, PILOT_BBOX.west],
  [PILOT_BBOX.north, PILOT_BBOX.east],
];
