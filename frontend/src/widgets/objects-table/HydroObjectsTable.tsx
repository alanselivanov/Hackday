import type { EnrichedHydroFacility } from '@/entities/facility/model/types';
import { StatusBadge } from '@/shared/ui/StatusBadge';
import styles from './HydroObjectsTable.module.css';

interface HydroObjectsTableProps {
  facilities: EnrichedHydroFacility[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export function HydroObjectsTable({
  facilities,
  selectedId,
  onSelect,
}: HydroObjectsTableProps) {
  return (
    <div className={styles.wrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Type</th>
            <th>District</th>
            <th>Technical condition</th>
            <th>Wear %</th>
            <th>Fact efficiency</th>
            <th>Status</th>
            <th>Risk score</th>
          </tr>
        </thead>
        <tbody>
          {facilities.map((facility) => {
            const isSelected = facility.id === selectedId;

            return (
              <tr
                key={facility.id}
                className={isSelected ? styles.selected : undefined}
                onClick={() => onSelect(facility.id)}
              >
                <td>{facility.id}</td>
                <td className={styles.nameCell}>{facility.name}</td>
                <td>{facility.facility_type_label}</td>
                <td>{facility.district}</td>
                <td>{facility.technical_condition ?? '—'}</td>
                <td>{facility.wear_percentage.toFixed(1)}</td>
                <td>
                  {facility.efficiency_fact != null
                    ? facility.efficiency_fact.toFixed(2)
                    : '—'}
                </td>
                <td>
                  <StatusBadge
                    status={facility.repair_status}
                    label={facility.repair_status_label}
                  />
                </td>
                <td className={styles.riskCell}>{facility.risk_score}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {facilities.length === 0 && (
        <p className={styles.empty}>No objects match the current filters.</p>
      )}
    </div>
  );
}
