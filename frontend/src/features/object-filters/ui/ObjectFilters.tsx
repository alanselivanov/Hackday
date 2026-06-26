import type { ObjectFiltersState } from '@/entities/facility/model/types';
import { FACILITY_TYPE_LABELS, REPAIR_STATUS_LABELS } from '@/shared/config/constants';
import { Button } from '@/shared/ui/Button';
import styles from './ObjectFilters.module.css';

interface ObjectFiltersProps {
  filters: ObjectFiltersState;
  technicalConditions: string[];
  waterSources: string[];
  districts: string[];
  ruralDistricts: string[];
  onChange: (filters: ObjectFiltersState) => void;
  onReset: () => void;
  resultCount: number;
}

export function ObjectFilters({
  filters,
  technicalConditions,
  waterSources,
  districts,
  ruralDistricts,
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
          <span className={styles.label}>Поиск</span>
          <input
            type="search"
            placeholder="Название, район, сельский округ..."
            value={filters.search}
            onChange={(e) => update({ search: e.target.value })}
            className={styles.input}
          />
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Тип</span>
          <select
            value={filters.facility_type}
            onChange={(e) =>
              update({
                facility_type: e.target.value as ObjectFiltersState['facility_type'],
              })
            }
            className={styles.select}
          >
            <option value="all">Все типы</option>
            {Object.entries(FACILITY_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Статус</span>
          <select
            value={filters.repair_status}
            onChange={(e) =>
              update({
                repair_status: e.target.value as ObjectFiltersState['repair_status'],
              })
            }
            className={styles.select}
          >
            <option value="all">Все статусы</option>
            {Object.entries(REPAIR_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Техническое состояние</span>
          <select
            value={filters.technical_condition}
            onChange={(e) => update({ technical_condition: e.target.value })}
            className={styles.select}
          >
            <option value="all">Все состояния</option>
            {technicalConditions.map((condition) => (
              <option key={condition} value={condition}>
                {condition}
              </option>
            ))}
            <option value="unknown">Нет данных</option>
          </select>
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Водоисточник</span>
          <select
            value={filters.water_source}
            onChange={(e) => update({ water_source: e.target.value })}
            className={styles.select}
          >
            <option value="all">Все источники</option>
            {waterSources.map((source) => (
              <option key={source} value={source}>
                {source}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Район</span>
          <select
            value={filters.district}
            onChange={(e) => update({ district: e.target.value })}
            className={styles.select}
          >
            <option value="all">Все районы</option>
            {districts.map((district) => (
              <option key={district} value={district}>
                {district}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Сельский округ</span>
          <select
            value={filters.rural_district}
            onChange={(e) => update({ rural_district: e.target.value })}
            className={styles.select}
          >
            <option value="all">Все округа</option>
            {ruralDistricts.map((district) => (
              <option key={district} value={district}>
                {district}
              </option>
            ))}
            <option value="unknown">Нет данных</option>
          </select>
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Аварийность</span>
          <select
            value={filters.emergency}
            onChange={(e) =>
              update({ emergency: e.target.value as ObjectFiltersState['emergency'] })
            }
            className={styles.select}
          >
            <option value="all">Все объекты</option>
            <option value="yes">Повышенная аварийность</option>
            <option value="no">Без аварийного флага</option>
          </select>
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Износ от, %</span>
          <input
            type="number"
            min="0"
            max="100"
            value={filters.min_wear}
            onChange={(e) => update({ min_wear: e.target.value })}
            className={styles.input}
          />
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Износ до, %</span>
          <input
            type="number"
            min="0"
            max="100"
            value={filters.max_wear}
            onChange={(e) => update({ max_wear: e.target.value })}
            className={styles.input}
          />
        </label>

        <label className={styles.field}>
          <span className={styles.label}>КПД факт. от</span>
          <input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={filters.min_efficiency_fact}
            onChange={(e) => update({ min_efficiency_fact: e.target.value })}
            className={styles.input}
          />
        </label>

        <div className={styles.actions}>
          <Button variant="ghost" size="sm" onClick={onReset}>
            Сбросить
          </Button>
        </div>
      </div>

      <p className={styles.meta}>
        Найдено объектов: <strong>{resultCount}</strong>
      </p>
    </div>
  );
}
