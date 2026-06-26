import { DataImportPanel } from '@/features/data-import/ui/DataImportPanel';
import { Card } from '@/shared/ui/Card';
import styles from './ImportDataPage.module.css';

interface ImportDataPageProps {
  onImported: () => Promise<void>;
}

export function ImportDataPage({ onImported }: ImportDataPageProps) {
  return (
    <section className={styles.page}>
      <div>
        <h2 className={styles.title}>Добавление сооружений и постов</h2>
        <p className={styles.subtitle}>
          Загрузите CSV или Excel-файл. Backend разберёт строки и добавит гидротехнические
          сооружения, гидропосты и связанные параметры в базу данных.
        </p>
      </div>

      <DataImportPanel onImported={onImported} />

      <div className={styles.grid}>
        <Card padding="md">
          <h3 className={styles.cardTitle}>Что можно загрузить</h3>
          <ul className={styles.list}>
            <li>каналы, шлюзы, водозаборы, насосные станции, плотины/дамбы;</li>
            <li>гидрологические посты с координатами и параметрами телеметрии;</li>
            <li>поля Excel/CSV сопоставляются с backend-схемой импорта.</li>
          </ul>
        </Card>

        <Card padding="md">
          <h3 className={styles.cardTitle}>Требования к файлу</h3>
          <ul className={styles.list}>
            <li>формат: <code>.csv</code>, <code>.xlsx</code> или <code>.xls</code>;</li>
            <li>желательно наличие названия, типа объекта, района и координат;</li>
            <li>после успешной загрузки карта и реестр обновятся из БД.</li>
          </ul>
        </Card>
      </div>
    </section>
  );
}
