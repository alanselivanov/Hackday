import type { FacilityType, RepairStatus } from '@/entities/facility/model/types';

export const FACILITY_TYPE_LABELS: Record<FacilityType, string> = {
  canal: 'Canal',
  post: 'Hydrological post',
  sluice: 'Sluice',
  intake: 'Water intake',
  pumping: 'Pumping station',
  dam_dyke: 'Dam / dyke',
};

export const REPAIR_STATUS_LABELS: Record<RepairStatus, string> = {
  normal: 'Normal',
  inspection_required: 'Need inspection',
  repair_required: 'Need repair',
  critical: 'Critical',
};

export const REPAIR_STATUS_COLORS: Record<RepairStatus, string> = {
  normal: '#22c55e',
  inspection_required: '#eab308',
  repair_required: '#f97316',
  critical: '#ef4444',
};

/** Pilot segment of the Irtysh River (Pavlodar region, KZ) — [lat, lng] */
export const IRTYSH_PILOT_POLYLINE: [number, number][] = [
  [52.48, 76.52],
  [52.46, 76.68],
  [52.43, 76.84],
  [52.40, 77.00],
  [52.37, 77.16],
  [52.34, 77.32],
  [52.31, 77.48],
  [52.28, 77.64],
];

export const PILOT_MAP_CENTER: [number, number] = [52.38, 77.08];

export const PILOT_MAP_BOUNDS: [[number, number], [number, number]] = [
  [52.24, 76.46],
  [52.52, 77.72],
];
