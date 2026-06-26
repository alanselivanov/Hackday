import { useState } from 'react';
import type { EnrichedHydroFacility } from '@/entities/facility/model/types';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { useDashboardStats } from '@/pages/dashboard/useDashboardData';
import styles from './ReportsPage.module.css';

interface ReportsPageProps {
  facilities: EnrichedHydroFacility[];
}

function toCsv(facilities: EnrichedHydroFacility[]) {
  const rows = [
    ['№', 'Название', 'Тип', 'Район', 'Статус', 'Износ %', 'КПД факт.'],
    ...facilities.map((facility, index) => [
      index + 1,
      facility.name,
      facility.facility_type_label,
      facility.district,
      facility.repair_status_label ?? '',
      facility.wear_percentage,
      facility.efficiency_fact ?? '',
    ]),
  ];

  return rows
    .map((row) =>
      row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(';'),
    )
    .join('\n');
}

export function ReportsPage({ facilities }: ReportsPageProps) {
  const [generatedAt, setGeneratedAt] = useState<string | null>(null);
  const stats = useDashboardStats(facilities);

  const generateReport = () => {
    setGeneratedAt(new Date().toLocaleString('ru-RU'));
  };

  const downloadCsv = () => {
    const blob = new Blob([toCsv(facilities)], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'hydro-facilities-report.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className={styles.page}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>Отчёты по гидротехническим сооружениям</h2>
          <p className={styles.subtitle}>
            Сформируйте оперативный отчёт по объектам и состоянию на основе данных из БД.
          </p>
        </div>
        <div className={styles.actions}>
          <Button onClick={generateReport}>Сформировать отчёт</Button>
          <Button variant="ghost" onClick={() => window.print()}>
            Печать
          </Button>
          <Button variant="ghost" onClick={downloadCsv}>
            Скачать CSV
          </Button>
        </div>
      </div>

      <div className={styles.report}>
        <Card padding="md">
          <h3 className={styles.cardTitle}>Сводка</h3>
          <dl className={styles.summary}>
            <div><dt>Всего объектов</dt><dd>{stats.total}</dd></div>
            <div><dt>Норма</dt><dd>{stats.normal}</dd></div>
            <div><dt>Требуется осмотр</dt><dd>{stats.inspection}</dd></div>
            <div><dt>Требуется ремонт</dt><dd>{stats.repair}</dd></div>
            <div><dt>Критическое состояние</dt><dd>{stats.critical}</dd></div>
          </dl>
          <p className={styles.meta}>
            {generatedAt ? `Отчёт сформирован: ${generatedAt}` : 'Отчёт ещё не сформирован'}
          </p>
        </Card>
      </div>
    </section>
  );
}
