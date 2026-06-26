import styles from './AppSidebar.module.css';

export type SidebarPage = 'dashboard' | 'registry' | 'import' | 'reports';

const NAV_ITEMS: Array<{ id: SidebarPage; label: string }> = [
  { id: 'dashboard', label: 'Дашборд' },
  { id: 'registry', label: 'Реестр объектов' },
  { id: 'import', label: 'Добавить данные' },
  { id: 'reports', label: 'Отчёты' },
];

interface AppSidebarProps {
  activePage: SidebarPage;
  onNavigate: (page: SidebarPage) => void;
}

export function AppSidebar({ activePage, onNavigate }: AppSidebarProps) {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.titleBlock}>
        <span className={styles.title}>Каталог ГТС</span>
        <span className={styles.subtitle}>участок р. Иртыш</span>
      </div>

      <nav className={styles.nav} aria-label="Основная навигация">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={item.id === activePage ? `${styles.navItem} ${styles.active}` : styles.navItem}
            onClick={() => onNavigate(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
