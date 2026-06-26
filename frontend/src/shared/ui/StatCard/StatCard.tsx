import { Card } from '@/shared/ui/Card';
import styles from './StatCard.module.css';

interface StatCardProps {
  label: string;
  value: string | number;
  accent?: 'default' | 'green' | 'yellow' | 'orange' | 'red' | 'teal';
}

export function StatCard({ label, value, accent = 'default' }: StatCardProps) {
  return (
    <Card padding="sm" className={styles.statCard}>
      <span className={styles.label}>{label}</span>
      <span className={`${styles.value} ${styles[accent]}`}>{value}</span>
    </Card>
  );
}
