import type { ObjectFiltersState } from '@/entities/facility/model/types';
import { FACILITY_TYPE_LABELS, REPAIR_STATUS_LABELS } from '@/shared/config/constants';
import { Button } from '@/shared/ui/Button';
import styles from './ObjectFilters.module.css';

interface ObjectFiltersProps {
  filters: ObjectFiltersState;
  technicalConditions: string[];
  onChange: (filters: ObjectFiltersState) => void;
  onReset: () => void;
  resultCount: number;
}

export function ObjectFilters({
  filters,
  technicalConditions,
  onChange,
  onReset,
  resultCount,
}: ObjectFiltersProps) {
  const update = (patch: Partial<ObjectFiltersState>) => {
    onChange({ ...filters, ...patch });
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.row}>
        <label className={styles.field}>
          <span className={styles.label}>Search</span>
          <input
            type="search"
            placeholder="Name, district, rural district…"
            value={filters.search}
            onChange={(e) => update({ search: e.target.value })}
            className={styles.input}
          />
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Type</span>
          <select
            value={filters.facility_type}
            onChange={(e) =>
              update({
                facility_type: e.target.value as ObjectFiltersState['facility_type'],
              })
            }
            className={styles.select}
          >
            <option value="all">All types</option>
            {Object.entries(FACILITY_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Status</span>
          <select
            value={filters.repair_status}
            onChange={(e) =>
              update({
                repair_status: e.target.value as ObjectFiltersState['repair_status'],
              })
            }
            className={styles.select}
          >
            <option value="all">All statuses</option>
            {Object.entries(REPAIR_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Technical condition</span>
          <select
            value={filters.technical_condition}
            onChange={(e) => update({ technical_condition: e.target.value })}
            className={styles.select}
          >
            <option value="all">All conditions</option>
            {technicalConditions.map((condition) => (
              <option key={condition} value={condition}>
                {condition}
              </option>
            ))}
            <option value="unknown">Unknown / not set</option>
          </select>
        </label>

        <div className={styles.actions}>
          <Button variant="ghost" size="sm" onClick={onReset}>
            Reset filters
          </Button>
        </div>
      </div>

      <p className={styles.meta}>
        Showing <strong>{resultCount}</strong> object{resultCount === 1 ? '' : 's'}
      </p>
    </div>
  );
}
