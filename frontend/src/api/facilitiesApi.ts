import type { EnrichedHydroFacility, FacilityType, HydroFacility } from '@/entities/facility/model/types';
import { FACILITY_TYPE_LABELS } from '@/shared/config/constants';

interface ApiLocation {
  type: 'Point';
  coordinates: [number, number];
}

interface ApiFacility {
  id: number;
  facility_type: FacilityType;
  facility_type_display?: string;
  name: string;
  water_source: string | null;
  district: string | null;
  rural_district: string | null;
  cadastral_number: string | null;
  state_act: string | null;
  location: ApiLocation | null;
  year_built: number | null;
  year_balanced: number | null;
  wear_percentage: number | null;
  technical_condition: string | null;
  efficiency_project: number | null;
  efficiency_fact: number | null;
  is_emergency_prone: boolean;
  analytics?: {
    repair_status?: HydroFacility['repair_status'];
    repair_status_display?: string | null;
    inspection_interval_days?: number | null;
    next_inspection_date?: string | null;
    calculated_importance?: HydroFacility['calculated_importance'];
    calculated_importance_display?: string | null;
  } | null;
  specific?: Record<string, unknown>;
}

interface FacilitiesResponse {
  count: number;
  filters: { facility_type: string | null };
  available_types: Array<{ value: FacilityType; label: string }>;
  results: ApiFacility[];
}

export interface ImportFacilitiesResult {
  created?: number;
  skipped_duplicates?: number;
  conflicts?: unknown[];
  warnings?: unknown[];
  unmapped_columns?: unknown[];
  error?: string;
  [key: string]: unknown;
}

function normalizeFacility(apiFacility: ApiFacility, index: number): EnrichedHydroFacility | null {
  if (!apiFacility.location?.coordinates) {
    return null;
  }

  const [lng, lat] = apiFacility.location.coordinates;
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    return null;
  }

  const analytics = apiFacility.analytics;

  return {
    id: apiFacility.id,
    map_label: `Объект ${index + 1}`,
    facility_type: apiFacility.facility_type,
    facility_type_label:
      apiFacility.facility_type_display ?? FACILITY_TYPE_LABELS[apiFacility.facility_type],
    name: apiFacility.name,
    water_source: apiFacility.water_source ?? '—',
    district: apiFacility.district ?? '—',
    rural_district: apiFacility.rural_district,
    cadastral_number: apiFacility.cadastral_number,
    state_act: apiFacility.state_act,
    location: { lat, lng },
    year_built: apiFacility.year_built,
    year_balanced: apiFacility.year_balanced,
    wear_percentage: apiFacility.wear_percentage ?? 0,
    technical_condition: apiFacility.technical_condition,
    efficiency_project: apiFacility.efficiency_project,
    efficiency_fact: apiFacility.efficiency_fact,
    is_emergency_prone: apiFacility.is_emergency_prone,
    calculated_importance: analytics?.calculated_importance ?? null,
    calculated_importance_display: analytics?.calculated_importance_display ?? null,
    repair_status: analytics?.repair_status ?? null,
    repair_status_label: analytics?.repair_status_display ?? null,
    inspection_interval_days: analytics?.inspection_interval_days ?? null,
    next_inspection_date: analytics?.next_inspection_date ?? null,
    specific: apiFacility.specific ?? {},
  };
}

export async function fetchFacilities(): Promise<EnrichedHydroFacility[]> {
  const response = await fetch('/api/facilities/');

  if (!response.ok) {
    throw new Error(`Не удалось загрузить объекты: HTTP ${response.status}`);
  }

  const data = (await response.json()) as FacilitiesResponse;

  return data.results
    .map(normalizeFacility)
    .filter((facility): facility is EnrichedHydroFacility => facility !== null);
}

export async function importFacilitiesFile(file: File): Promise<ImportFacilitiesResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/import/', {
    method: 'POST',
    body: formData,
  });
  const body = (await response.json()) as ImportFacilitiesResult;

  if (!response.ok) {
    throw new Error(body.error ?? `Ошибка импорта: HTTP ${response.status}`);
  }

  return body;
}
