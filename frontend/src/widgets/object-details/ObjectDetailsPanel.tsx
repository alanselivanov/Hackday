import type { EnrichedHydroFacility } from '@/entities/facility/model/types';
import { StatusBadge } from '@/shared/ui/StatusBadge';
import styles from './ObjectDetailsPanel.module.css';

interface ObjectDetailsPanelProps {
  facility: EnrichedHydroFacility | null;
}

function DetailRow({ label, value }: { label: string; value: string | number | null | undefined }) {
  const display = value == null || value === '' ? '—' : String(value);

  return (
    <div className={styles.row}>
      <dt className={styles.label}>{label}</dt>
      <dd className={styles.value}>{display}</dd>
    </div>
  );
}

export function ObjectDetailsPanel({ facility }: ObjectDetailsPanelProps) {
  if (!facility) {
    return (
      <div className={styles.empty}>
        <p>Select an object on the map or table to view details.</p>
      </div>
    );
  }

  return (
    <div className={styles.panel}>
      <header className={styles.header}>
        <h3 className={styles.title}>{facility.name}</h3>
        <p className={styles.subtitle}>{facility.facility_type_label}</p>
        <StatusBadge status={facility.repair_status} label={facility.repair_status_label} />
      </header>

      <dl className={styles.list}>
        <DetailRow label="Water source" value={facility.water_source} />
        <DetailRow label="District" value={facility.district} />
        <DetailRow
          label="Coordinates"
          value={`${facility.location.lat.toFixed(4)}, ${facility.location.lng.toFixed(4)}`}
        />
        <DetailRow label="Year built" value={facility.year_built} />
        <DetailRow label="Year balanced" value={facility.year_balanced} />
        <DetailRow label="Wear %" value={facility.wear_percentage.toFixed(1)} />
        <DetailRow label="Technical condition" value={facility.technical_condition} />
        <DetailRow
          label="Efficiency (project)"
          value={facility.efficiency_project?.toFixed(2)}
        />
        <DetailRow label="Efficiency (fact)" value={facility.efficiency_fact?.toFixed(2)} />
        <DetailRow label="Importance" value={facility.calculated_importance} />
        <DetailRow label="Next inspection" value={facility.next_inspection_date} />
        <DetailRow label="Risk score" value={facility.risk_score} />
      </dl>

      <section className={styles.recommendation}>
        <h4>Recommendation</h4>
        <p>{facility.recommendation}</p>
      </section>
    </div>
  );
}
