import { useRef, useState } from 'react';
import { importFacilitiesFile, type ImportFacilitiesResult } from '@/api/facilitiesApi';
import { Button } from '@/shared/ui/Button';
import styles from './DataImportPanel.module.css';

interface DataImportPanelProps {
  onImported: () => Promise<void>;
}

function formatResult(result: ImportFacilitiesResult | null) {
  if (!result) return null;

  return [
    `Создано: ${result.created ?? 0}`,
    `Дубли: ${result.skipped_duplicates ?? 0}`,
    `Конфликты: ${Array.isArray(result.conflicts) ? result.conflicts.length : 0}`,
    `Предупреждения: ${Array.isArray(result.warnings) ? result.warnings.length : 0}`,
    `Несопоставленные колонки: ${
      Array.isArray(result.unmapped_columns) ? result.unmapped_columns.length : 0
    }`,
  ].join(' · ');
}

export function DataImportPanel({ onImported }: DataImportPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ImportFacilitiesResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    const file = inputRef.current?.files?.[0];
    if (!file) {
      setError('Выберите файл .xlsx, .xls или .csv');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const importResult = await importFacilitiesFile(file);
      setResult(importResult);
      await onImported();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Ошибка импорта');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.panel}>
      <div>
        <h2 className={styles.title}>Импорт данных</h2>
        <p className={styles.hint}>
          Загрузка Excel/CSV через backend endpoint <code>/api/import/</code>
        </p>
      </div>

      <div className={styles.controls}>
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          className={styles.input}
        />
        <Button size="sm" onClick={handleUpload} disabled={isLoading}>
          {isLoading ? 'Загрузка...' : 'Загрузить'}
        </Button>
      </div>

      {result && <p className={styles.success}>{formatResult(result)}</p>}
      {error && <p className={styles.error}>{error}</p>}
    </div>
  );
}
