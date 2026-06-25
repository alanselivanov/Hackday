import { useMemo, useState } from 'react';
import { fetchFacilities } from '@/api/facilitiesApi';
import { ObjectFilters } from '@/features/object-filters/ui/ObjectFilters';
import { Card } from '@/shared/ui/Card';
import { StatCard } from '@/shared/ui/StatCard';
import { StatusBadge } from '@/shared/ui/StatusBadge';
import { AnalyticsCharts } from '@/widgets/analytics/AnalyticsCharts';
import { DashboardHeader } from '@/widgets/dashboard-header/DashboardHeader';
import { ObjectDetailsPanel } from '@/widgets/object-details/ObjectDetailsPanel';
import { HydroObjectsTable } from '@/widgets/objects-table/HydroObjectsTable';
import { PilotMap } from '@/widgets/pilot-map/PilotMap';
import styles from './DashboardPage.module.css';
import {
  DEFAULT_FILTERS,
  getTechnicalConditions,
  useDashboardStats,
  useFilteredFacilities,
} from './useDashboardData';

export function DashboardPage() {
  const allFacilities = useMemo(() => fetchFacilities(), []);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const filteredFacilities = useFilteredFacilities(allFacilities, filters);
  const stats = useDashboardStats(allFacilities);
  const technicalConditions = useMemo(
    () => getTechnicalConditions(allFacilities),
    [allFacilities],
  );

  const selectedFacility =
    allFacilities.find((f) => f.id === selectedId) ?? null;

  const handleResetFilters = () => setFilters(DEFAULT_FILTERS);

  return (
    <div className={styles.page}>
      <DashboardHeader />

      <section className={styles.statsRow}>
        <StatCard label="Total facilities" value={stats.total} accent="teal" />
        <StatCard label="Normal" value={stats.normal} accent="green" />
        <StatCard label="Need inspection" value={stats.inspection} accent="yellow" />
        <StatCard label="Need repair" value={stats.repair} accent="orange" />
        <StatCard label="Critical" value={stats.critical} accent="red" />
        <StatCard label="Average risk score" value={stats.avgRisk} accent="teal" />
      </section>

      <section className={styles.mapSection}>
        <Card padding="sm" className={styles.mapCard}>
          <h2 className={styles.sectionTitle}>Interactive map — pilot segment</h2>
          <PilotMap
            facilities={filteredFacilities}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </Card>

        <Card padding="md" className={styles.detailsCard}>
          <h2 className={styles.sectionTitle}>Object details</h2>
          <ObjectDetailsPanel facility={selectedFacility} />
        </Card>
      </section>

      <section className={styles.riskSection}>
        <Card padding="md">
          <h2 className={styles.sectionTitle}>Highest-risk objects</h2>
          <ul className={styles.riskList}>
            {stats.topRisk.map((facility) => (
              <li key={facility.id}>
                <button
                  type="button"
                  className={
                    facility.id === selectedId
                      ? `${styles.riskItem} ${styles.riskItemSelected}`
                      : styles.riskItem
                  }
                  onClick={() => setSelectedId(facility.id)}
                >
                  <span className={styles.riskName}>{facility.name}</span>
                  <span className={styles.riskMeta}>
                    <StatusBadge
                      status={facility.repair_status}
                      label={facility.repair_status_label}
                    />
                    <span className={styles.riskScore}>{facility.risk_score}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </Card>
      </section>

      <section className={styles.tableSection}>
        <h2 className={styles.sectionTitle}>Catalog objects</h2>
        <ObjectFilters
          filters={filters}
          technicalConditions={technicalConditions}
          onChange={setFilters}
          onReset={handleResetFilters}
          resultCount={filteredFacilities.length}
        />
        <HydroObjectsTable
          facilities={filteredFacilities}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
      </section>

      <section>
        <h2 className={styles.sectionTitle}>Analytics overview</h2>
        <AnalyticsCharts facilities={allFacilities} />
      </section>

      <section>
        <Card padding="lg" className={styles.explanation}>
          <h2 className={styles.explanationTitle}>Rule-based assessment model</h2>
          <p className={styles.explanationText}>
            The system classifies hydraulic structures using technical condition,
            commissioning year, efficiency, wear level, emergency flag, inspection date
            and data completeness. The model can later be extended with GIS-based
            detection, satellite imagery and machine learning.
          </p>
        </Card>
      </section>
    </div>
  );
}
