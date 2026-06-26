import { useMemo } from 'react';
import type {
  EnrichedHydroFacility,
  ObjectFiltersState,
} from '@/entities/facility/model/types';

export const DEFAULT_FILTERS: ObjectFiltersState = {
  search: '',
  facility_type: 'all',
  repair_status: 'all',
  technical_condition: 'all',
  water_source: 'all',
  district: 'all',
  rural_district: 'all',
  emergency: 'all',
  min_wear: '',
  max_wear: '',
  min_efficiency_fact: '',
};

export function useFilteredFacilities(
  facilities: EnrichedHydroFacility[],
  filters: ObjectFiltersState,
) {
  return useMemo(() => {
    const query = filters.search.trim().toLowerCase();

    return facilities.filter((facility) => {
      if (filters.facility_type !== 'all' && facility.facility_type !== filters.facility_type) {
        return false;
      }

      if (filters.repair_status !== 'all' && facility.repair_status !== filters.repair_status) {
        return false;
      }

      if (filters.technical_condition !== 'all') {
        if (filters.technical_condition === 'unknown') {
          if (facility.technical_condition) return false;
        } else if (facility.technical_condition !== filters.technical_condition) {
          return false;
        }
      }

      if (filters.water_source !== 'all' && facility.water_source !== filters.water_source) {
        return false;
      }

      if (filters.district !== 'all' && facility.district !== filters.district) {
        return false;
      }

      if (filters.rural_district !== 'all') {
        if (filters.rural_district === 'unknown') {
          if (facility.rural_district) return false;
        } else if (facility.rural_district !== filters.rural_district) {
          return false;
        }
      }

      if (filters.emergency !== 'all') {
        const expected = filters.emergency === 'yes';
        if (facility.is_emergency_prone !== expected) return false;
      }

      const minWear = Number(filters.min_wear);
      if (filters.min_wear !== '' && Number.isFinite(minWear)) {
        if (facility.wear_percentage < minWear) return false;
      }

      const maxWear = Number(filters.max_wear);
      if (filters.max_wear !== '' && Number.isFinite(maxWear)) {
        if (facility.wear_percentage > maxWear) return false;
      }

      const minEfficiency = Number(filters.min_efficiency_fact);
      if (filters.min_efficiency_fact !== '' && Number.isFinite(minEfficiency)) {
        if (facility.efficiency_fact == null || facility.efficiency_fact < minEfficiency) {
          return false;
        }
      }

      if (!query) return true;

      const haystack = [
        facility.name,
        facility.water_source,
        facility.district,
        facility.rural_district ?? '',
        facility.technical_condition ?? '',
        facility.cadastral_number ?? '',
        facility.state_act ?? '',
      ]
        .join(' ')
        .toLowerCase();

      return haystack.includes(query);
    });
  }, [facilities, filters]);
}

export function useDashboardStats(facilities: EnrichedHydroFacility[]) {
  return useMemo(() => {
    const total = facilities.length;
    const normal = facilities.filter((f) => f.repair_status === 'normal').length;
    const inspection = facilities.filter(
      (f) => f.repair_status === 'inspection_required',
    ).length;
    const repair = facilities.filter((f) => f.repair_status === 'repair_required').length;
    const critical = facilities.filter((f) => f.repair_status === 'critical').length;

    return { total, normal, inspection, repair, critical };
  }, [facilities]);
}

export function getTechnicalConditions(facilities: EnrichedHydroFacility[]): string[] {
  const set = new Set<string>();
  facilities.forEach((f) => {
    if (f.technical_condition) set.add(f.technical_condition);
  });
  return Array.from(set).sort();
}

export function getUniqueValues(
  facilities: EnrichedHydroFacility[],
  field: 'water_source' | 'district' | 'rural_district',
): string[] {
  const set = new Set<string>();
  facilities.forEach((facility) => {
    const value = facility[field];
    if (value) set.add(value);
  });
  return Array.from(set).sort((a, b) => a.localeCompare(b, 'ru'));
}
