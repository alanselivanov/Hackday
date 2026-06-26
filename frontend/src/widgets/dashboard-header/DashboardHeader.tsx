import styles from './DashboardHeader.module.css';

export function DashboardHeader() {
  const today = new Date().toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

  return (
    <header className={styles.header}>
      <div className={styles.mainRow}>
        <div className={styles.brand}>
          <h1 className={styles.title}>Мониторинг гидротехнических сооружений</h1>
          <p className={styles.subtitle}>Пилотный участок реки Иртыш · Павлодарская область</p>
        </div>

        <div className={styles.aside}>
          <span className={styles.date}>{today}</span>
          <span className={styles.modeBadge}>демонстрационный режим</span>
        </div>
      </div>
    </header>
  );
}
