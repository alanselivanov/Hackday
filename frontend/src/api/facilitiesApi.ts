import { MOCK_FACILITIES } from '@/api/mocks/mockFacilities';
import type { EnrichedHydroFacility } from '@/entities/facility/model/types';
import { enrichFacility } from '@/features/risk-assessment/model/riskAssessment';

export function fetchFacilities(): EnrichedHydroFacility[] {
  return MOCK_FACILITIES.map(enrichFacility);
}
