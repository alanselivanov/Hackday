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

function formatSpecificValue(value: unknown) {
  if (value == null || value === '') return '—';
  if (typeof value === 'boolean') return value ? 'Да' : 'Нет';
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(2);
  return String(value);
}

export function ObjectDetailsPanel({ facility }: ObjectDetailsPanelProps) {
  if (!facility) {
    return (
      <div className={styles.empty}>
        <p>Выберите объект на карте или в таблице, чтобы посмотреть детали.</p>
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
        <DetailRow label="Водоисточник" value={facility.water_source} />
        <DetailRow label="Район" value={facility.district} />
        <DetailRow label="Сельский округ" value={facility.rural_district} />
        <DetailRow label="Кадастровый N" value={facility.cadastral_number} />
        <DetailRow label="Госакт" value={facility.state_act} />
        <DetailRow
          label="Координаты"
          value={`${facility.location.lat.toFixed(4)}, ${facility.location.lng.toFixed(4)}`}
        />
        <DetailRow label="Год ввода" value={facility.year_built} />
        <DetailRow label="Год на балансе" value={facility.year_balanced} />
        <DetailRow label="Износ, %" value={facility.wear_percentage.toFixed(1)} />
        <DetailRow label="Тех. состояние" value={facility.technical_condition} />
        <DetailRow label="Статус ремонта" value={facility.repair_status_label} />
        <DetailRow
          label="КПД проектный"
          value={facility.efficiency_project?.toFixed(2)}
        />
        <DetailRow label="КПД фактический" value={facility.efficiency_fact?.toFixed(2)} />
        <DetailRow
          label="Аварийность"
          value={facility.is_emergency_prone ? 'Повышенная' : 'Нет флага'}
        />
        <DetailRow
          label="Важность"
          value={facility.calculated_importance_display}
        />
        <DetailRow
          label="Интервал осмотра, дней"
          value={facility.inspection_interval_days}
        />
        <DetailRow label="Следующий осмотр" value={facility.next_inspection_date} />
      </dl>

      {facility.specific && Object.keys(facility.specific).length > 0 && (
        <section className={styles.specific}>
          <h4>Параметры типа объекта</h4>
          <dl className={styles.list}>
            {Object.entries(facility.specific).map(([key, value]) => (
              <DetailRow key={key} label={key} value={formatSpecificValue(value)} />
            ))}
          </dl>
        </section>
      )}

    </div>
  );
}
