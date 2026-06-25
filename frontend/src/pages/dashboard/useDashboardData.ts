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

      if (!query) return true;

      const haystack = [
        facility.name,
        facility.district,
        facility.rural_district ?? '',
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
    const avgRisk =
      total === 0
        ? 0
        : Math.round(
            facilities.reduce((sum, f) => sum + f.risk_score, 0) / total,
          );

    const topRisk = [...facilities]
      .sort((a, b) => b.risk_score - a.risk_score)
      .slice(0, 5);

    return { total, normal, inspection, repair, critical, avgRisk, topRisk };
  }, [facilities]);
}

export function getTechnicalConditions(facilities: EnrichedHydroFacility[]): string[] {
  const set = new Set<string>();
  facilities.forEach((f) => {
    if (f.technical_condition) set.add(f.technical_condition);
  });
  return Array.from(set).sort();
}
