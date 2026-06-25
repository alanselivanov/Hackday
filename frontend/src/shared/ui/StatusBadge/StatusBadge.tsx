import type { RepairStatus } from '@/entities/facility/model/types';
import { REPAIR_STATUS_COLORS } from '@/shared/config/constants';
import styles from './StatusBadge.module.css';

interface StatusBadgeProps {
  status: RepairStatus;
  label: string;
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const color = REPAIR_STATUS_COLORS[status];

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
      {label}
    </span>
  );
}
