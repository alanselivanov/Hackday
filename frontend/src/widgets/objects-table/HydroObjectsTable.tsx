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
            <th>№</th>
            <th>Название</th>
            <th>Тип</th>
            <th>Район</th>
            <th>Тех. состояние</th>
            <th>Износ, %</th>
            <th>КПД факт.</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          {facilities.map((facility, index) => {
            const isSelected = facility.id === selectedId;

            return (
              <tr
                key={facility.id}
                className={isSelected ? styles.selected : undefined}
                onClick={() => onSelect(facility.id)}
              >
                <td>{index + 1}</td>
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
              </tr>
            );
          })}
        </tbody>
      </table>

      {facilities.length === 0 && (
        <p className={styles.empty}>По текущим фильтрам объекты не найдены.</p>
      )}
    </div>
  );
}
