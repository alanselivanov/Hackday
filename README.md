# Hackday — реестр и мониторинг гидротехнических сооружений

Проект состоит из двух частей:

- `Backend/hydro_registry` — Django 5.2 + GeoDjango + PostgreSQL/PostGIS.
- `frontend` — React + TypeScript + Vite.

Система показывает гидротехнические сооружения на карте, ведёт реестр, импортирует данные из OpenStreetMap и Excel/CSV, рассчитывает периодичность осмотров и статус необходимости ремонта.

## Возможности

- Интерактивная карта сооружений с координатами.
- Реестр объектов с фильтрацией и поиском.
- Карточки объектов: тип, район, водоисточник, износ, техническое состояние, координаты.
- Аналитика по объекту:
  - `repair_status` — норма / требуется осмотр / требуется ремонт / критическое состояние;
  - `inspection_interval_days` — рекомендуемый период осмотра;
  - `next_inspection_date` — дата следующего осмотра;
  - `calculated_importance` — важность объекта;
  - `condition_score` и причины статуса.
- Импорт объектов из OpenStreetMap через Overpass API.
- Импорт `.xlsx`, `.xls`, `.csv` через API и frontend.
- Автоматическое создание mock-данных и mock-осмотров для демонстрации.
- Пересчёт аналитики для всех объектов одной командой.
- Django Admin для просмотра и ручного редактирования данных.

## Структура

```text
Hackday/
├── README.md
├── Plan2.md
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── api/
│       ├── pages/
│       ├── widgets/
│       ├── features/
│       ├── entities/
│       └── shared/
└── Backend/
    └── hydro_registry/
        ├── manage.py
        ├── requirements.txt
        ├── .env.example
        ├── QUICKSTART.md
        ├── inspection_service.py
        ├── hydro_registry/
        ├── core/
        ├── infrastructure/
        ├── monitoring/
        ├── analytics/
        ├── osm_import/
        └── ingestion/
```

## Требования

Backend:

- Python 3.11+
- PostgreSQL 16+
- PostGIS
- GDAL/GEOS для GeoDjango

Frontend:

- Node.js 20+
- npm

На Windows для GeoDjango обычно нужны DLL из PostgreSQL/PostGIS, например:


## Настройка базы данных

Создайте PostgreSQL-базу и включите PostGIS:

```sql
CREATE DATABASE hydro_registry;
\c hydro_registry
CREATE EXTENSION postgis;
```

Если используете pgAdmin, extension можно создать через Query Tool:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

## Запуск backend

Перейдите в папку backend:

```powershell
cd Backend\hydro_registry
```

Создайте и активируйте виртуальное окружение:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Установите зависимости:

```powershell
pip install -r requirements.txt
```

Для импорта Excel/CSV через LLM может понадобиться OpenRouter-клиент:

```powershell
pip install openrouter
```

Создайте `.env`:

```powershell
copy .env.example .env
```

Пример `.env`:

```env
DB_NAME=hydro_registry
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

Примените миграции:

```powershell
python manage.py migrate
```

Проверьте проект:

```powershell
python manage.py check
```

Запустите backend:

```powershell
python manage.py runserver
```

Backend будет доступен по адресу:

```text
http://127.0.0.1:8000
```

Админка:

```text
http://127.0.0.1:8000/admin/
```

Создание администратора:

```powershell
python manage.py createsuperuser
```

## Запуск frontend

Во втором терминале перейдите в папку frontend:

```powershell
cd frontend
```

Установите зависимости:

```powershell
npm install
```

Запустите dev-сервер:

```powershell
npm run dev
```

Frontend будет доступен по адресу:

```text
http://localhost:5173
```

В `frontend/vite.config.ts` настроен proxy:

```ts
'/api' -> 'http://127.0.0.1:8000'
```

Поэтому backend должен быть запущен параллельно.

Production-сборка:

```powershell
npm run build
npm run preview
```

## Быстрый запуск всего проекта

Терминал 1:

```powershell
cd Backend\hydro_registry
.venv\Scripts\activate
python manage.py runserver
```

Терминал 2:

```powershell
cd frontend
npm run dev
```

Откройте:

```text
http://localhost:5173
```

## Наполнение данными

### Импорт из OpenStreetMap

Команда запрашивает Overpass API, классифицирует объекты, создаёт сооружения, mock-характеристики, mock-осмотры и пересчитывает аналитику.

```powershell
cd Backend\hydro_registry
python manage.py import_osm_facilities
```

Очистить OSM-импорт перед повторным импортом:

```powershell
python manage.py clear_osm_import
```

Область импорта задаётся в:

```text
Backend/hydro_registry/osm_import/services/region.py
```

Константы:

```python
SOUTH = ...
WEST = ...
NORTH = ...
EAST = ...
```

### Импорт Excel/CSV

Через frontend:

```text
http://localhost:5173
```

Раздел:

```text
Добавить данные
```

Через API:

```powershell
curl -X POST http://127.0.0.1:8000/api/import/ -F "file=@data.xlsx"
```

Поддерживаемые форматы:

- `.xlsx`
- `.xls`
- `.csv`

Импорт Excel/CSV делает:

- парсинг файла;
- сопоставление колонок с полями моделей;
- создание сооружений;
- создание `InspectionLog`, если в файле есть поля осмотра;
- расчёт периода осмотра;
- расчёт статуса ремонта.


### Пересчёт аналитики

Если данные уже есть в базе и нужно заново пересчитать статусы и интервалы:

```powershell
python manage.py recalculate_facility_analytics
```

Команда применяет алгоритмы ко всем объектам:

- `inspection_service.run_for_facility()` — период осмотра;
- `analytics.services.recalculate_status()` — статус ремонта.

## API

### Получить все сооружения

```http
GET /api/facilities/
```

Пример:

```text
http://127.0.0.1:8000/api/facilities/
```

Фильтр по типу:

```http
GET /api/facilities/?facility_type=canal
GET /api/facilities/?facility_type=canal,sluice,pumping
```

Доступные типы:

- `canal` — канал
- `post` — гидропост
- `sluice` — шлюз
- `intake` — водозабор
- `pumping` — насосная станция
- `dam_dyke` — плотина/дамба

Формат ответа:

```json
{
  "count": 1,
  "filters": {
    "facility_type": null
  },
  "available_types": [
    { "value": "canal", "label": "Канал" }
  ],
  "results": [
    {
      "id": 1,
      "facility_type": "canal",
      "facility_type_display": "Канал",
      "name": "Канал A",
      "water_source": "Иртыш",
      "district": "Импорт OSM",
      "location": {
        "type": "Point",
        "coordinates": [76.85, 52.3]
      },
      "wear_percentage": 30.5,
      "technical_condition": "удовлетворительное",
      "analytics": {
        "repair_status": "repair_required",
        "repair_status_display": "Требуется ремонт",
        "inspection_interval_days": 421,
        "next_inspection_date": "2027-08-21",
        "calculated_importance": "medium",
        "calculated_importance_display": "Средняя",
        "condition_score": 33.3,
        "repair_status_reason": {
          "factors": []
        },
        "requires_verification": false
      },
      "specific": {
        "capacity": 10.0,
        "total_length": 2.5
      }
    }
  ]
}
```

### Импорт файла

```http
POST /api/import/
```

Поле формы:

```text
file
```

Пример ответа:

```json
{
  "created": 3,
  "skipped_duplicates": 0,
  "conflicts": [],
  "warnings": [],
  "unmapped_columns": [],
  "facilities": []
}
```

### Demo-страницы импорта

В проекте также есть временные demo-страницы:

```text
/demo/import/
/demo/import/run/
/demo/import/sample.csv
```

Они нужны для демонстрации импорта без полноценного frontend-потока.

## Что можно делать во frontend

### Дашборд

Файл:

```text
frontend/src/pages/dashboard/DashboardPage.tsx
```

Функции:

- смотреть карту объектов;
- видеть KPI по статусам;
- выбирать объект на карте;
- смотреть панель деталей;
- фильтровать критичные объекты;
- смотреть графики и сводки.

### Реестр

Файл:

```text
frontend/src/pages/registry/RegistryPage.tsx
```

Функции:

- смотреть таблицу всех сооружений;
- фильтровать и искать объекты;
- сравнивать типы, районы, износ, статусы;
- открывать данные по объектам.

### Добавить данные

Файл:

```text
frontend/src/pages/import-data/ImportDataPage.tsx
```

Функции:

- загрузить `.csv`, `.xlsx`, `.xls`;
- отправить файл на `/api/import/`;
- получить отчёт об импорте;
- увидеть ошибки, конфликты и несопоставленные колонки.

### Отчёты

Файл:

```text
frontend/src/pages/reports/ReportsPage.tsx
```

Функции:

- смотреть сводную аналитику;
- выгружать отчёты;
- анализировать распределение объектов по состоянию.

## Как работает аналитика

В проекте есть два основных расчётных модуля.

### Период осмотра

Файл:

```text
Backend/hydro_registry/inspection_service.py
```

Рассчитывает:

- `inspection_interval_days`
- `next_inspection_date`
- факторы расчёта периода осмотра

На расчёт влияют:

- класс ГТС (`safety_class`);
- износ;
- возраст;
- техническое состояние;
- аварийность;
- сезонный риск;
- падение КПД;
- тип последнего осмотра.

### Статус ремонта

Файл:

```text
Backend/hydro_registry/analytics/services.py
```

Рассчитывает:

- `repair_status`
- `condition_score`
- `requires_verification`
- причины статуса

Статусы:

- `normal` — норма
- `inspection_required` — требуется осмотр
- `repair_required` — требуется ремонт
- `critical` — критическое состояние

На статус влияют:

- трещины;
- фильтрация;
- деформации;
- поломка оборудования;
- заиление;
- фактический износ по осмотру;
- критерии безопасности K1/K2;
- просроченный срок осмотра.

## Основные backend-приложения

- `core` — базовая модель `BaseHydroFacility`, API списка объектов.
- `infrastructure` — каналы, шлюзы, водозаборы, насосные станции, плотины/дамбы.
- `monitoring` — гидропосты и журнал осмотров.
- `analytics` — аналитика, критерии безопасности, пересчёт статусов.
- `osm_import` — импорт из OpenStreetMap.
- `ingestion` — импорт Excel/CSV.

## Проверки и тесты

Проверить Django-конфигурацию:

```powershell
python manage.py check
```

Запустить тесты OSM-импорта:

```powershell
python manage.py test osm_import
```

Запустить тесты импорта файлов:

```powershell
python manage.py test ingestion
```

Собрать frontend:

```powershell
cd frontend
npm run build
```

## Частые проблемы

### `GDAL not found`

Укажите пути в `.env`:

```env
GDAL_LIBRARY_PATH=C:\Program Files\PostgreSQL\16\bin\libgdal-35.dll
GEOS_LIBRARY_PATH=C:\Program Files\PostgreSQL\16\bin\libgeos_c.dll
```

### `type "geometry" does not exist`

В базе не включён PostGIS:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

### `/api/facilities/` падает на отсутствующей колонке

Примените миграции:

```powershell
python manage.py migrate
```

### Frontend не видит backend

Проверьте, что backend запущен:

```text
http://127.0.0.1:8000/api/facilities/
```

Frontend ходит на backend через Vite proxy `/api -> http://127.0.0.1:8000`.

### Excel/CSV импорт не работает без OpenRouter

Либо установите и настройте OpenRouter:

```powershell
pip install openrouter
```

```env
OPEN_ROUTER=your_key
```

Либо включите оффлайн-эвристику:

```env
INGESTION_FAKE_MAPPER=1
```

## Полезные адреса

- Frontend: `http://localhost:5173`
- Backend API: `http://127.0.0.1:8000/api/facilities/`
- Импорт файла: `http://127.0.0.1:8000/api/import/`
- Admin: `http://127.0.0.1:8000/admin/`
- Demo import: `http://127.0.0.1:8000/demo/import/`
