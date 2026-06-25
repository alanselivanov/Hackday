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
  facility_type: FacilityType;
  facility_type_label: string;
  name: string;
  water_source: string;
  district: string;
  rural_district?: string | null;
  location: FacilityLocation;
  year_built?: number | null;
  year_balanced?: number | null;
  wear_percentage: number;
  technical_condition?: string | null;
  efficiency_project?: number | null;
  efficiency_fact?: number | null;
  is_emergency_prone: boolean;
  calculated_importance?: ImportanceLevel | null;
  next_inspection_date?: string | null;
}

export interface EnrichedHydroFacility extends HydroFacility {
  repair_status: RepairStatus;
  repair_status_label: string;
  risk_score: number;
  recommendation: string;
}

export interface ObjectFiltersState {
  search: string;
  facility_type: FacilityType | 'all';
  repair_status: RepairStatus | 'all';
  technical_condition: string;
}
