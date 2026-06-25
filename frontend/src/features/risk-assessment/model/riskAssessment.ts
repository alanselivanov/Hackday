import type { HydroFacility, RepairStatus } from '@/entities/facility/model/types';
import { REPAIR_STATUS_LABELS } from '@/shared/config/constants';

function hasMissingData(facility: HydroFacility): boolean {
  return (
    facility.year_built == null ||
    facility.efficiency_fact == null ||
    facility.technical_condition == null ||
    facility.next_inspection_date == null
  );
}

function isOverdueInspection(nextInspectionDate: string | null | undefined): boolean {
  if (!nextInspectionDate) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const deadline = new Date(nextInspectionDate);
  return deadline < today;
}

export function calculateRiskScore(facility: HydroFacility): number {
  let score = 0;

  const condition = facility.technical_condition?.toLowerCase().trim() ?? '';
  if (condition === 'не удов.' || condition.includes('неудов')) {
    score += 35;
  } else if (condition === 'удовл.' || condition.includes('удовл')) {
    score += 5;
  }

  if (facility.wear_percentage > 70) {
    score += 30;
  } else if (facility.wear_percentage > 40) {
    score += 18;
  } else if (facility.wear_percentage > 20) {
    score += 8;
  }

  if (facility.efficiency_fact != null && facility.efficiency_fact < 0.55) {
    score += 20;
  } else if (facility.efficiency_fact != null && facility.efficiency_fact < 0.7) {
    score += 10;
  }

  if (facility.year_built != null && facility.year_built < 1950) {
    score += 15;
  } else if (facility.year_built != null && facility.year_built < 1970) {
    score += 8;
  }

  if (facility.is_emergency_prone) {
    score += 25;
  }

  if (isOverdueInspection(facility.next_inspection_date)) {
    score += 12;
  }

  if (hasMissingData(facility)) {
    score += 8;
  }

  if (facility.calculated_importance === 'high') {
    score += 10;
  } else if (facility.calculated_importance === 'medium') {
    score += 5;
  }

  return Math.min(100, Math.round(score));
}

export function calculateRepairStatus(facility: HydroFacility): RepairStatus {
  const score = calculateRiskScore(facility);

  if (score >= 80) return 'critical';
  if (score >= 55) return 'repair_required';
  if (score >= 30) return 'inspection_required';
  return 'normal';
}

export function getRecommendation(facility: HydroFacility): string {
  const status = calculateRepairStatus(facility);
  const score = calculateRiskScore(facility);

  if (status === 'critical') {
    return `Immediate intervention required (risk score ${score}). Restrict operation, schedule emergency inspection and prepare repair plan within 7 days.`;
  }

  if (status === 'repair_required') {
    return `Plan capital repair within the current season (risk score ${score}). Prioritize structural assessment and budget allocation.`;
  }

  if (status === 'inspection_required') {
    return `Schedule field inspection within 30 days (risk score ${score}). Verify wear readings and update technical condition records.`;
  }

  return `Continue routine monitoring (risk score ${score}). Maintain scheduled inspections and telemetry checks.`;
}

export function enrichFacility(facility: HydroFacility) {
  const risk_score = calculateRiskScore(facility);
  const repair_status = calculateRepairStatus(facility);

  return {
    ...facility,
    risk_score,
    repair_status,
    repair_status_label: REPAIR_STATUS_LABELS[repair_status],
    recommendation: getRecommendation(facility),
  };
}
