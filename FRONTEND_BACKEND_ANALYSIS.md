# Анализ backend и подготовка к frontend

> Дата анализа: 25.06.2026  
> Проект: AITU Hackday — веб-портал визуализации и анализа гидротехнических сооружений (pilot segment реки Иртыш)

---

## 1. Структура проекта

```
AITU/
└── Hackday/                          # git-репозиторий (ветки: main, dilyara-feature)
    ├── README.md                     # пустой
    └── Backend/
        └── hydro_registry/           # Django 5.2 + GeoDjango + PostgreSQL/PostGIS
            ├── manage.py
            ├── requirements.txt
            ├── QUICKSTART.md         # инструкция по запуску
            ├── .env.example
            ├── hydro_registry/       # settings, urls, wsgi/asgi
            ├── core/                 # базовая модель объектов
            ├── infrastructure/       # каналы, шлюзы, водозаборы, НС, плотины
            ├── monitoring/           # гидропосты, журнал осмотров
            └── analytics/            # аналитика и статусы объектов
```

**Frontend отсутствует.** Папок `frontend/`, `Frontend/`, `web/`, `client/` или React/Vite-проекта в репозитории нет.

**Слои backend (текущее состояние):**

| Слой | Статус |
|------|--------|
| **Models** | Реализованы во всех 4 приложениях |
| **Migrations** | Есть (`0001_initial` в каждом app) |
| **Admin** | Заглушки (модели не зарегистрированы) |
| **Views / Controllers** | Заглушки (пустые файлы) |
| **Services** | Отсутствуют |
| **Serializers / Schemas** | Отсутствуют (Django REST Framework не подключён) |
| **URLs / Routes** | Только `/admin/` |
| **Tests** | Заглушки |
| **Fixtures / seed data** | Отсутствуют |

---

## 2. Где находится backend

**Путь:** `Hackday/Backend/hydro_registry/`

**Стек:**
- Python 3 + Django 5.2
- GeoDjango (`django.contrib.gis`)
- PostgreSQL + PostGIS
- `python-dotenv` для переменных окружения
- `psycopg2-binary` для подключения к БД

**Зависимости** (`requirements.txt`):
```
Django>=5.2,<5.3
psycopg2-binary>=2.9
python-dotenv>=1.0
```

Django REST Framework, CORS, Celery и прочие API-библиотеки **не установлены**.

---

## 3. Как запускается backend

Подробная инструкция — в `Backend/hydro_registry/QUICKSTART.md`.

**Кратко:**

1. Установить PostgreSQL 16+ и PostGIS (`CREATE EXTENSION postgis;` в БД).
2. Создать виртуальное окружение и установить зависимости:
   ```bash
   cd Hackday/Backend/hydro_registry
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   pip install -r requirements.txt
   ```
3. Скопировать `.env.example` → `.env`, указать параметры БД.
4. Применить миграции:
   ```bash
   python manage.py migrate
   ```
5. (Опционально) создать суперпользователя для админки:
   ```bash
   python manage.py createsuperuser
   ```
6. Запустить dev-сервер:
   ```bash
   python manage.py runserver
   ```

**Доступ после запуска:** http://127.0.0.1:8000/admin/

На Windows может потребоваться PostGIS bundle / OSGeo4W и переменные `GDAL_LIBRARY_PATH`, `GEOS_LIBRARY_PATH` (см. QUICKSTART.md и `settings.py`).

---

## 4. Существующие API endpoints

На момент анализа **публичного REST API нет**.

Единственный зарегистрированный маршрут (`hydro_registry/urls.py`):

| Method | Endpoint | Описание |
|--------|----------|----------|
| * | `/admin/` | Django Admin (HTML, требует auth) |

Файлы `views.py` во всех приложениях пустые — бизнес-логика и HTTP-обработчики не реализованы.

---

## 5. Доменные сущности (models)

Backend содержит **полноценную модель данных**, но без API-слоя.

### 5.1. Базовый объект — `core.BaseHydroFacility`

Общая сущность для всех гидротехнических объектов (multi-table inheritance).

| Поле | Тип | Назначение для frontend |
|------|-----|-------------------------|
| `id` | PK | Идентификатор на карте / в деталях |
| `facility_type` | enum | Тип маркера и иконка |
| `uid` | float | № по реестру |
| `name` | string | Название на карте и в карточке |
| `water_source` | string | Фильтр по водоисточнику (Иртыш) |
| `district` | string | Район |
| `rural_district` | string | Сельский округ |
| `cadastral_number` | string | Кадастровый номер |
| `state_act` | string | Гос. акт |
| **`location`** | **PointField (SRID 4326)** | **lat/lng для карты** |
| `year_built` | int | Год ввода |
| `year_balanced` | int | Год на балансе |
| `wear_percentage` | float | % износа |
| `technical_condition` | string | Текстовое тех. состояние |
| `efficiency_project` / `efficiency_fact` | float | КПД |
| `is_emergency_prone` | bool | Флаг аварийности |

**Типы объектов (`facility_type`):**
- `canal` — Канал
- `post` — Гидропост
- `sluice` — Шлюз
- `intake` — Водозабор
- `pumping` — Насосная станция
- `dam_dyke` — Плотина/Дамба

### 5.2. Гидротехнические сооружения — `infrastructure`

| Модель | Наследует | Специфичные поля |
|--------|-----------|------------------|
| `Canal` | BaseHydroFacility | capacity, total_length, earth_length, lined_length, area_*, bottom_width, top_width, depth |
| `Sluice` | BaseHydroFacility | gates_count, gate_type, drive_type, max_discharge |
| `WaterIntake` | BaseHydroFacility | intake_type, is_gravity, fish_protection, max_volume_clean |
| `PumpingStation` | BaseHydroFacility | pumps_count, installed_power, current_consumption, head_pressure |
| `DamsAndDykes` | BaseHydroFacility | material, crest_length, max_height, reservoir_volume, is_declared_dangerous |

### 5.3. Мониторинг — `monitoring`

| Модель | Описание |
|--------|----------|
| `HydroPost` | Гидропост: post_type, equipment_installed, current_water_level, critical_water_level, last_telemetry_at |
| `InspectionLog` | Журнал осмотров (FK → BaseHydroFacility): inspection_date, inspector_name, дефекты (трещины, заиление, фильтрация, деформация, поломки), detected_wear_override |

### 5.4. Аналитика и статус — `analytics.FacilityAnalytics`

OneToOne к `BaseHydroFacility`.

| Поле | Значения | Назначение |
|------|----------|------------|
| **`repair_status`** | `normal`, `inspection_required`, `repair_required`, `critical` | **Цвет маркера / badge на карте** |
| `inspection_interval_days` | int | Рекомендуемая частота осмотра |
| `next_inspection_date` | date | Дедлайн следующего осмотра |
| `calculated_importance` | `low`, `medium`, `high` | Приоритет объекта |
| `updated_at` | datetime | Время последнего расчёта |

**Статусы полностью соответствуют требованиям ТЗ:**
- норма → `normal`
- требуется осмотр → `inspection_required`
- требуется ремонт → `repair_required`
- критическое состояние → `critical`

### 5.5. Чего нет в моделях

- Отдельной сущности «pilot segment Иртыш» (фильтрация через `water_source` или будущее поле `river_segment`)
- LineString / Polygon для протяжённости каналов (только точка `location`)
- Модели интеграции внешних источников данных
- Фото/документов осмотров
- Пользовательских ролей для frontend (только стандартный Django User)

---

## 6. Какие данные backend уже может отдавать

**Сейчас — ничего через HTTP API.**

Данные существуют только на уровне ORM/PostgreSQL после миграций и ручного наполнения (админка, скрипты, SQL). Публичных JSON-ответов нет.

Потенциально backend **готов отдавать** (после реализации API):

- список всех объектов с координатами и типом;
- детальную карточку объекта с type-specific полями;
- статус (`repair_status`) и аналитику;
- историю осмотров;
- телеметрию гидропостов (уровень воды, critical level);
- агрегаты для дашборда (кол-во по статусам, по типам, по районам).

---

## 7. Недостающие endpoints для frontend

Рекомендуемый минимальный REST API (префикс `/api/v1/`):

### Карта и объекты

| Method | Endpoint | Назначение |
|--------|----------|------------|
| GET | `/api/v1/facilities/` | Список объектов для карты (GeoJSON или JSON с lat/lng) |
| GET | `/api/v1/facilities/{id}/` | Детальная карточка (base + subtype fields) |
| GET | `/api/v1/facilities/geojson/` | GeoJSON FeatureCollection для Leaflet/MapLibre |
| GET | `/api/v1/facilities/?facility_type=canal` | Фильтр по типу |
| GET | `/api/v1/facilities/?water_source=Иртыш` | Фильтр pilot segment |
| GET | `/api/v1/facilities/?repair_status=critical` | Фильтр по статусу |
| GET | `/api/v1/facilities/?district=...` | Фильтр по району |
| GET | `/api/v1/facilities/bbox/?min_lat=&min_lng=&max_lat=&max_lng=` | Объекты в viewport карты |

### Осмотры

| Method | Endpoint | Назначение |
|--------|----------|------------|
| GET | `/api/v1/facilities/{id}/inspections/` | История осмотров объекта |
| GET | `/api/v1/inspections/{id}/` | Детали осмотра |

### Гидропосты / телеметрия

| Method | Endpoint | Назначение |
|--------|----------|------------|
| GET | `/api/v1/hydroposts/` | Список постов с текущим уровнем |
| GET | `/api/v1/hydroposts/{id}/telemetry/` | Текущие показания (пока только last value в модели) |

### Аналитика

| Method | Endpoint | Назначение |
|--------|----------|------------|
| GET | `/api/v1/analytics/summary/` | Сводка: count по repair_status, facility_type, district |
| GET | `/api/v1/analytics/by-status/` | Распределение статусов для charts |
| GET | `/api/v1/analytics/critical/` | Список критических объектов |
| GET | `/api/v1/analytics/overdue-inspections/` | Просроченные осмотры (next_inspection_date < today) |

### Справочники

| Method | Endpoint | Назначение |
|--------|----------|------------|
| GET | `/api/v1/meta/facility-types/` | Enum типов объектов |
| GET | `/api/v1/meta/repair-statuses/` | Enum статусов с labels |
| GET | `/api/v1/meta/districts/` | Уникальные районы |

### Интеграция (на перспективу)

| Method | Endpoint | Назначение |
|--------|----------|------------|
| POST | `/api/v1/integrations/telemetry/` | Webhook/import телеметрии |
| POST | `/api/v1/integrations/registry/` | Импорт из внешнего реестра |

### Инфраструктура API

- `GET /api/v1/health/` — healthcheck
- CORS для frontend origin (например `http://localhost:5173`)
- OpenAPI/Swagger schema (`/api/schema/`, `/api/docs/`)

---

## 8. Поля, необходимые frontend

### Минимальный объект для маркера на карте

```json
{
  "id": 1,
  "facility_type": "sluice",
  "facility_type_label": "Шлюз",
  "name": "Шлюз №3",
  "location": { "lat": 54.87, "lng": 69.15 },
  "repair_status": "repair_required",
  "repair_status_label": "Требуется ремонт",
  "wear_percentage": 67.5,
  "is_emergency_prone": false,
  "calculated_importance": "high"
}
```

### Карточка объекта (detail panel)

**Общие поля:** все поля `BaseHydroFacility` + `analytics` + последний `InspectionLog`.

**Type-specific:** поля соответствующей модели (`Canal`, `Sluice`, …).

**Для гидропоста дополнительно:**
- `current_water_level`, `critical_water_level`, `last_telemetry_at`, `post_type`

### Дашборд аналитики

```json
{
  "total_facilities": 120,
  "by_status": {
    "normal": 80,
    "inspection_required": 25,
    "repair_required": 12,
    "critical": 3
  },
  "by_type": { "canal": 40, "sluice": 15, "post": 30, "...": "..." },
  "overdue_inspections": 8,
  "critical_objects": [...]
}
```

### Маппинг статусов → UI

| `repair_status` | Цвет (рекомендация) | Label |
|-----------------|---------------------|-------|
| `normal` | green | Норма |
| `inspection_required` | yellow | Требуется осмотр |
| `repair_required` | orange | Требуется ремонт |
| `critical` | red | Критическое состояние |

---

## 9. Что мокать на frontend, пока API нет

Поскольку REST API отсутствует, frontend на первом этапе должен работать с **mock data** (JSON fixtures или MSW).

### 9.1. Обязательные моки

1. **Список объектов на карте** — 15–30 точек в районе Иртыша (координаты ~54.8–55.2°N, 68.5–70.5°E), все 6 типов `facility_type`.
2. **Статусы** — распределение по 4 значениям `repair_status`.
3. **Детальные карточки** — 2–3 примера на каждый тип с subtype-полями.
4. **История осмотров** — 3–5 записей `InspectionLog` на объект.
5. **Analytics summary** — агрегаты для pie/bar charts.
6. **Гидропосты** — current/critical water level, last_telemetry_at.

### 9.2. Опциональные моки

- GeoJSON слой каналов (LineString) — в backend каналы только Point; для pilot UX можно нарисовать линии вручную.
- Time-series телеметрии — в модели только последнее значение; для графиков нужен mock history.
- Фильтры по `district`, `water_source`.
- Задержка сети / loading states для реалистичного UX.

### 9.3. Структура mock-слоя (рекомендация)

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts          # fetch wrapper, base URL из env
│   │   ├── facilities.ts      # типы + функции API
│   │   └── mocks/
│   │       ├── facilities.json
│   │       ├── inspections.json
│   │       └── analytics-summary.json
│   └── types/
│       └── facility.ts        # TypeScript interfaces по Django models
```

Переключение mock/real через `VITE_USE_MOCKS=true`.

---

## 10. Как лучше подключить frontend к backend

### 10.1. Рекомендуемая архитектура

```
Hackday/
├── Backend/hydro_registry/     # Django API (порт 8000)
└── Frontend/                   # React + Vite (порт 5173)
    └── .env → VITE_API_URL=http://127.0.0.1:8000/api/v1
```

### 10.2. Шаги на стороне backend (для backend-команды)

1. Добавить `djangorestframework`, `django-cors-headers`, `djangorestframework-gis`.
2. Создать `serializers.py` в каждом app (или общий `api/` package).
3. Реализовать ViewSets / APIViews + роутинг через `DefaultRouter`.
4. Включить CORS:
   ```python
   CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
   ```
5. GeoJSON-сериализация для `location` (DRF GIS).
6. Зарегистрировать модели в admin / management command для seed pilot data Иртыш.
7. (Опционально) `drf-spectacular` для OpenAPI — frontend сможет генерировать типы.

### 10.3. Шаги на стороне frontend

1. **Phase 1 (сейчас):** React + Leaflet/MapLibre + mock data, без зависимости от backend.
2. **Phase 2:** API client с typed interfaces, совпадающими с будущими serializers.
3. **Phase 3:** замена mocks на real API по endpoint-ам по мере готовности backend.
4. Proxy в dev (`vite.config.ts`):
   ```ts
   server: {
     proxy: {
       '/api': 'http://127.0.0.1:8000'
     }
   }
   ```

### 10.4. Контракт API ↔ frontend

- Формат координат: `{ "lat": number, "lng": number }` или GeoJSON `Point` (lon, lat).
- Даты: ISO 8601 (`YYYY-MM-DD`, `YYYY-MM-DDTHH:mm:ssZ`).
- Enum-значения: snake_case как в Django models (`repair_required`, не «Требуется ремонт»); labels — отдельное поле или справочник `/meta/`.
- Пагинация: `?page=1&page_size=50` (DRF PageNumberPagination).
- Ошибки: стандартный DRF `{ "detail": "..." }`.

### 10.5. Pilot segment Иртыш

До появления отдельного поля в модели:
- фильтровать по `water_source` (строка «Иртыш» / «р. Иртыш»);
- или hardcode bbox viewport на frontend;
- согласовать с backend единый критерий pilot segment.

---

## 11. Выводы

| Аспект | Статус |
|--------|--------|
| Модель данных | ✅ Хорошо проработана, покрывает ТЗ |
| Статусы (4 уровня) | ✅ Есть в `FacilityAnalytics.repair_status` |
| Координаты | ✅ `PointField` SRID 4326 |
| Осмотры | ✅ `InspectionLog` |
| Гидропосты | ✅ `HydroPost` + телеметрия |
| Аналитика | ✅ Модель есть, расчётная логика — нет |
| REST API | ❌ Не реализован |
| Frontend | ❌ Отсутствует |
| Seed data (Иртыш) | ❌ Отсутствует |
| Admin UI | ⚠️ Маршрут есть, модели не зарегистрированы |

**Frontend можно начинать параллельно на mocks**, используя поля из Django models как контракт типов. Backend-команда может добавлять endpoints по приоритету: `facilities/` → `analytics/summary/` → `inspections/` → фильтры и GeoJSON.

---

## 12. Приоритет реализации API (для согласования с backend)

1. `GET /api/v1/facilities/` — разблокирует карту
2. `GET /api/v1/facilities/{id}/` — карточка объекта
3. `GET /api/v1/analytics/summary/` — дашборд
4. `GET /api/v1/facilities/{id}/inspections/` — история осмотров
5. Фильтры + bbox + GeoJSON
6. Seed command с pilot data по Иртышу
