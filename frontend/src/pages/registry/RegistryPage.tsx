import type { EnrichedHydroFacility, ObjectFiltersState } from '@/entities/facility/model/types';
import { ObjectFilters } from '@/features/object-filters/ui/ObjectFilters';
import { HydroObjectsTable } from '@/widgets/objects-table/HydroObjectsTable';
import styles from './RegistryPage.module.css';

interface RegistryPageProps {
  facilities: EnrichedHydroFacility[];
  filteredFacilities: EnrichedHydroFacility[];
  filters: ObjectFiltersState;
  selectedId: number | null;
  technicalConditions: string[];
  waterSources: string[];
  districts: string[];
  ruralDistricts: string[];
  onChangeFilters: (filters: ObjectFiltersState) => void;
  onResetFilters: () => void;
  onSelect: (id: number) => void;
}

export function RegistryPage({
  facilities,
  filteredFacilities,
  filters,
  selectedId,
  technicalConditions,
  waterSources,
  districts,
  ruralDistricts,
  onChangeFilters,
  onResetFilters,
  onSelect,
}: RegistryPageProps) {
  return (
    <section className={styles.page}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>Реестр объектов участка</h2>
          <p className={styles.subtitle}>
            Поиск и фильтры по полному перечню сооружений ({facilities.length} в базе)
          </p>
        </div>
      </div>

      <div className={styles.content}>
        <ObjectFilters
          filters={filters}
          technicalConditions={technicalConditions}
          waterSources={waterSources}
          districts={districts}
          ruralDistricts={ruralDistricts}
          onChange={onChangeFilters}
          onReset={onResetFilters}
          resultCount={filteredFacilities.length}
        />
        <HydroObjectsTable
          facilities={filteredFacilities}
          selectedId={selectedId}
          onSelect={onSelect}
        />
      </div>
    </section>
  );
}
