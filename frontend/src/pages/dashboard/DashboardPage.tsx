import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchFacilities } from '@/api/facilitiesApi';
import type { EnrichedHydroFacility } from '@/entities/facility/model/types';
import { ImportDataPage } from '@/pages/import-data/ImportDataPage';
import { RegistryPage } from '@/pages/registry/RegistryPage';
import { ReportsPage } from '@/pages/reports/ReportsPage';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { StatCard } from '@/shared/ui/StatCard';
import { AnalyticsCharts } from '@/widgets/analytics/AnalyticsCharts';
import { AppSidebar, type SidebarPage } from '@/widgets/app-sidebar/AppSidebar';
import { DashboardHeader } from '@/widgets/dashboard-header/DashboardHeader';
import { ObjectDetailsPanel } from '@/widgets/object-details/ObjectDetailsPanel';
import { PilotMap } from '@/widgets/pilot-map/PilotMap';
import styles from './DashboardPage.module.css';
import {
  DEFAULT_FILTERS,
  getTechnicalConditions,
  getUniqueValues,
  useDashboardStats,
  useFilteredFacilities,
} from './useDashboardData';

export function DashboardPage() {
  const [activePage, setActivePage] = useState<SidebarPage>('dashboard');
  const [allFacilities, setAllFacilities] = useState<EnrichedHydroFacility[]>([]);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mapFullscreen, setMapFullscreen] = useState(false);
  const [criticalOnly, setCriticalOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadFacilities = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);

    try {
      const facilities = await fetchFacilities();
      setAllFacilities(facilities);
      setSelectedId((currentId) =>
        currentId != null && facilities.some((facility) => facility.id === currentId)
          ? currentId
          : null,
      );
    } catch (caughtError) {
      setLoadError(
        caughtError instanceof Error
          ? caughtError.message
          : 'Не удалось загрузить данные из backend',
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadFacilities();
  }, [loadFacilities]);

  const filteredFacilities = useFilteredFacilities(allFacilities, filters);
  const mapFacilities = useMemo(() => {
    if (!criticalOnly) return allFacilities;
    return allFacilities.filter((facility) => facility.repair_status === 'critical');
  }, [allFacilities, criticalOnly]);

  const stats = useDashboardStats(allFacilities);
  const technicalConditions = useMemo(
    () => getTechnicalConditions(allFacilities),
    [allFacilities],
  );
  const waterSources = useMemo(
    () => getUniqueValues(allFacilities, 'water_source'),
    [allFacilities],
  );
  const districts = useMemo(
    () => getUniqueValues(allFacilities, 'district'),
    [allFacilities],
  );
  const ruralDistricts = useMemo(
    () => getUniqueValues(allFacilities, 'rural_district'),
    [allFacilities],
  );
  const selectedFacility = allFacilities.find((facility) => facility.id === selectedId) ?? null;

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && mapFullscreen) {
        setMapFullscreen(false);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [mapFullscreen]);

  useEffect(() => {
    document.body.style.overflow = mapFullscreen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [mapFullscreen]);

  const handleResetFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setCriticalOnly(false);
  };

  const navigate = (page: SidebarPage) => {
    setMapFullscreen(false);
    setActivePage(page);
  };

  const renderDashboard = () => (
    <>
      <section className={styles.statsRow} aria-label="Сводные показатели">
        <StatCard label="Всего сооружений" value={stats.total} accent="teal" />
        <StatCard label="Норма" value={stats.normal} accent="green" />
        <StatCard label="Требуется осмотр" value={stats.inspection} accent="yellow" />
        <StatCard label="Требуется ремонт" value={stats.repair} accent="orange" />
        <StatCard label="Критическое состояние" value={stats.critical} accent="red" />
      </section>

      {loadError && (
        <Card padding="md" className={styles.errorCard}>
          <strong>Backend недоступен или вернул ошибку.</strong>
          <span>{loadError}</span>
          <Button size="sm" onClick={() => void loadFacilities()}>
            Повторить загрузку
          </Button>
        </Card>
      )}

      <section className={mapFullscreen ? styles.mapSectionFullscreen : styles.mapSection}>
        {!mapFullscreen && (
          <div className={styles.sectionHead}>
            <div>
              <h2 className={styles.sectionTitle}>Карта объектов</h2>
              <p className={styles.sectionHint}>
                Данные загружаются из backend endpoint <code>/api/facilities/</code>
              </p>
            </div>
            <div className={styles.sectionActions}>
              <Button
                variant={criticalOnly ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setCriticalOnly((value) => !value)}
              >
                {criticalOnly ? 'Показать все' : 'Только критичные'}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setSelectedId(null)}>
                Сбросить выбор
              </Button>
              {selectedId != null && (
                <Button variant="ghost" size="sm" onClick={() => navigate('registry')}>
                  К реестру
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={() => void loadFacilities()}>
                Обновить из БД
              </Button>
            </div>
          </div>
        )}

        {isLoading ? (
          <Card padding="lg" className={styles.loadingCard}>
            Загружаю объекты из базы данных...
          </Card>
        ) : (
          <div className={styles.mapLayout}>
            <Card padding="sm" className={styles.mapCard}>
              <PilotMap
                facilities={mapFacilities}
                selectedId={selectedId}
                onSelect={setSelectedId}
                isFullscreen={mapFullscreen}
                onToggleFullscreen={() => setMapFullscreen((value) => !value)}
              />
            </Card>

            <Card
              padding="md"
              className={mapFullscreen ? styles.fullscreenDetails : styles.detailsCard}
            >
              <h2 className={styles.panelTitle}>Карточка объекта</h2>
              <ObjectDetailsPanel facility={selectedFacility} />
            </Card>
          </div>
        )}
      </section>

      {!mapFullscreen && !isLoading && (
        <section>
          <h2 className={styles.sectionTitle}>Сводная аналитика</h2>
          <p className={styles.sectionHint}>Распределение по статусам, типам и районам</p>
          <AnalyticsCharts facilities={allFacilities} />
        </section>
      )}
    </>
  );

  return (
    <div className={styles.shell}>
      {!mapFullscreen && <AppSidebar activePage={activePage} onNavigate={navigate} />}

      <main className={styles.page}>
        {!mapFullscreen && <DashboardHeader />}

        {activePage === 'dashboard' && renderDashboard()}
        {activePage === 'registry' && (
          <RegistryPage
            facilities={allFacilities}
            filteredFacilities={filteredFacilities}
            filters={filters}
            selectedId={selectedId}
            technicalConditions={technicalConditions}
            waterSources={waterSources}
            districts={districts}
            ruralDistricts={ruralDistricts}
            onChangeFilters={setFilters}
            onResetFilters={handleResetFilters}
            onSelect={setSelectedId}
          />
        )}
        {activePage === 'import' && <ImportDataPage onImported={loadFacilities} />}
        {activePage === 'reports' && <ReportsPage facilities={allFacilities} />}
      </main>
    </div>
  );
}
