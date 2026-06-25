# Обзор архитектуры — endpoint импорта файлов

Синтез решений грилинга. Детали — в [ADR-0001](adr/0001-llm-maps-schema-not-data.md),
[ADR-0002](adr/0002-multi-sheet-merge-and-identity.md),
[ADR-0003](adr/0003-formats-and-endpoint-contract.md); термины — в [glossary.md](glossary.md).

## Поток данных

```
POST /api/import/  (multipart: файл)
        │
        ▼
[1] Парсер (Excel/CSV)
        │   • читает все листы
        │   • находит блок шапки, протягивает merge, строит флэт-имена
        │   • собирает 1–3 сэмпла данных под каждой колонкой
        ▼
[2] LLM-адаптер (OpenRouter, по листу)
        │   вход: флэт-имена + сэмплы + каталог целевых полей
        │   выход: { facility_type, mapping: {col_index → field} }
        ▼
[3] Раскладка (детерминированно, без LLM)
        │   каждая строка → dict значений по полям модели
        ▼
[4] Резолвер идентичности (PostGIS ST_DWithin ≤100м + water_source+name+year)
        │   совпало → skip · конфликт → report (не пишем) · нет ключа → warning
        ▼
[5] Репозиторий: создаёт BaseHydroFacility + подкласс
        ▼
[6] Отчёт об импорте (JSON)  →  клиент
```

## Раскладка по слоям (новое приложение `ingestion`)

Фича сквозная (касается `core` и всех подклассов), поэтому живёт в отдельном app, а не
размазана по существующим. Зависимости направлены внутрь: `domain` ничего не импортирует
из Django/IO.

```
ingestion/
  domain/                     # чистая логика, без Django и IO
    types.py                  # dataclasses: RawSheet, ColumnMapping, ResolvedRow,
                              #   Conflict, Warning, ImportReport
    field_catalog.py          # описания целевых полей по facility_type (вход в промпт)
    identity.py               # построение ключа идентичности, детект конфликтов
  application/
    import_service.py         # use-case: orchestration шагов [1]–[6]
  infrastructure/
    parsers/
      base.py                 # интерфейс FileParser
      excel_parser.py         # все листы, флэт шапки, merge fill, сэмплы
      csv_parser.py           # один плоский лист
    llm/
      openrouter_client.py    # адаптер: схема-маппинг (пакет openrouter, см. ADR-0003)
      prompt.py               # сборка промпта из field_catalog + запрет выдумывать
    persistence/
      facility_repository.py  # ST_DWithin дедуп, создание base+подкласс
  interfaces/
    views.py                  # POST /api/import/ (синхронно)
    urls.py
    serializers.py            # валидация загрузки + сериализация отчёта
```

Подключение: добавить `ingestion` в `INSTALLED_APPS`, `path("api/import/", ...)` в
`hydro_registry/urls.py`.

## Каталог целевых полей (вход в промпт LLM)

LLM маппит флэт-имена колонок на эти поля. **Не выдумывать значения; неизвестные колонки
не маппить; отсутствующие данные — пусто.**

### Общие (`BaseHydroFacility`, у всех типов)
`uid` (рег. №), `name` (наименование), `water_source` (водоисточник),
`district` (район), `rural_district` (сельский округ), `cadastral_number`,
`state_act` (акт), `year_built` (год ввода), `year_balanced` (год на баланс),
`wear_percentage` (% износа), `technical_condition` (тех. состояние),
`efficiency_project` (КПД проект.), `efficiency_fact` (КПД факт.),
`is_emergency_prone` (аварийность), `location` (координаты: широта/долгота → Point).

### `canal`
`capacity` (пропускная способность, м³/с), `total_length` (всего протяжённость, км),
`earth_length` (землян., км), `lined_length` (облицов., км),
`area_regular` (регулярное орошение, га), `area_liman` (лиманное, га),
`area_flooded` (обводнённое, га), `bottom_width`, `top_width`, `depth`.

### `sluice`
`gates_count`, `gate_type`, `drive_type`, `max_discharge`.

### `intake`
`intake_type`, `is_gravity`, `fish_protection`, `max_volume_clean`.

### `pumping`
`pumps_count`, `installed_power` (кВт), `current_consumption`, `head_pressure` (напор, м).

### `dam_dyke`
`material`, `crest_length`, `max_height`, `reservoir_volume` (млн м³), `is_declared_dangerous`.

### `post` (`HydroPost`)
`post_type`, `equipment_installed`, `current_water_level`, `critical_water_level`,
`last_telemetry_at`.

## Открытые риски / отложено
- **Пакет `openrouter`** может быть нестабилен → fallback на OpenAI-совместимый клиент
  (адаптер изолирован, см. ADR-0003).
- **Синхронный** endpoint может висеть на больших файлах; при необходимости — миграция на
  async/Celery позже.
- **Точность LLM-маппинга** на нетипичных шапках — митигируется сэмплами данных; карта
  логируется для аудита.
- **Координаты** обязательны для надёжной склейки; без них дедуп деградирует до warning.
- **`zip`/архивы и пакетная загрузка** — вне скоупа.

## Чек-лист реализации (следующий шаг, не часть грилинга)
1. `ingestion` app + регистрация в settings/urls.
2. `domain/types.py`, `domain/field_catalog.py`, `domain/identity.py`.
3. Парсеры Excel (флэт + merge fill + сэмплы) и CSV.
4. LLM-адаптер + промпт.
5. Репозиторий с `ST_DWithin`-дедупом.
6. `import_service` + view + сериализаторы.
7. Тесты на `датасет(1).xls` (3 листа, склейка, конфликты).
