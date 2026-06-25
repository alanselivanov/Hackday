import { Card } from '@/shared/ui/Card';
import styles from './DashboardHeader.module.css';

const META_CARDS = [
  { label: 'Pilot area', value: 'Irtysh River segment' },
  { label: 'Data source', value: 'Excel-based hydraulic structures catalog' },
  { label: 'Mode', value: 'Mock data / API-ready frontend' },
];

export function DashboardHeader() {
  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <div className={styles.logoMark} aria-hidden />
        <div>
          <h1 className={styles.title}>Irtysh Hydro Monitoring</h1>
          <p className={styles.subtitle}>
            Pilot segment digital catalog and condition analysis
          </p>
        </div>
      </div>

      <div className={styles.metaGrid}>
        {META_CARDS.map((item) => (
          <Card key={item.label} padding="sm" className={styles.metaCard}>
            <span className={styles.metaLabel}>{item.label}</span>
            <span className={styles.metaValue}>{item.value}</span>
          </Card>
        ))}
      </div>
    </header>
  );
}
