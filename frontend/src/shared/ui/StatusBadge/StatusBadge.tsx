import type { RepairStatus } from '@/entities/facility/model/types';
import { REPAIR_STATUS_COLORS } from '@/shared/config/constants';
import styles from './StatusBadge.module.css';

interface StatusBadgeProps {
  status: RepairStatus | null | undefined;
  label: string | null | undefined;
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const color = status ? REPAIR_STATUS_COLORS[status] : '#718096';

  return (
    <span
      className={styles.badge}
      style={{
        color,
        backgroundColor: `${color}18`,
        borderColor: `${color}40`,
      }}
    >
      <span className={styles.dot} style={{ backgroundColor: color }} />
      {label ?? '—'}
    </span>
  );
}
