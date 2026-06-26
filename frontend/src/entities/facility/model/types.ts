export type FacilityType =
  | 'canal'
  | 'post'
  | 'sluice'
  | 'intake'
  | 'pumping'
  | 'dam_dyke';

export type RepairStatus =
  | 'normal'
  | 'inspection_required'
  | 'repair_required'
  | 'critical';

export type ImportanceLevel = 'low' | 'medium' | 'high';

export interface FacilityLocation {
  lat: number;
  lng: number;
}

export interface HydroFacility {
  id: number;
  map_label?: string;
  facility_type: FacilityType;
  facility_type_label: string;
  name: string;
  water_source: string;
  district: string;
  rural_district?: string | null;
  cadastral_number?: string | null;
  state_act?: string | null;
  location: FacilityLocation;
  year_built?: number | null;
  year_balanced?: number | null;
  wear_percentage: number;
  technical_condition?: string | null;
  efficiency_project?: number | null;
  efficiency_fact?: number | null;
  is_emergency_prone: boolean;
  calculated_importance?: ImportanceLevel | null;
  calculated_importance_display?: string | null;
  repair_status?: RepairStatus | null;
  repair_status_label?: string | null;
  inspection_interval_days?: number | null;
  next_inspection_date?: string | null;
  specific?: Record<string, unknown>;
}

export interface EnrichedHydroFacility extends HydroFacility {
  repair_status: RepairStatus | null;
  repair_status_label: string | null;
}

export interface ObjectFiltersState {
  search: string;
  facility_type: FacilityType | 'all';
  repair_status: RepairStatus | 'all';
  technical_condition: string;
  water_source: string;
  district: string;
  rural_district: string;
  emergency: 'all' | 'yes' | 'no';
  min_wear: string;
  max_wear: string;
  min_efficiency_fact: string;
}
