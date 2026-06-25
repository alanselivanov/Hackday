# [ingestion] Скелет-проходчик: импорт каналов с одного листа

> **Триаж:** `ready-for-agent`
> **Источник:** [PRD — Endpoint импорта файлов](../prd/file-import-endpoint.md)
> (ADR [0001](../adr/0001-llm-maps-schema-not-data.md),
> [0003](../adr/0003-formats-and-endpoint-contract.md))

## What to build

Сквозной «тонкий» конвейер импорта на простейшем случае, задающий каркас всей фичи.
`POST /api/import/` (multipart, синхронный) принимает `.xlsx` с **одним листом и плоской
шапкой**, описывающий каналы, и создаёт записи в реестре. Файл проходит весь путь:
парсинг листа → определение `facility_type` и карты `колонка→поле` через LLM-порт →
детерминированная раскладка значений по полям → создание `BaseHydroFacility` + `Canal`
(multi-table inheritance) → синхронный JSON-отчёт `{ "created": N }`.

Заодно создаётся каркас приложения `ingestion` с чистыми слоями (domain без Django/IO,
application, infrastructure, interfaces), регистрация в `INSTALLED_APPS`, маршрут в
корневом `urls.py`, каталог целевых полей для общих полей `BaseHydroFacility` + полей
`Canal`, LLM-адаптер (пакет `openrouter`, модель `openrouter/auto`, ключ из `.env`) как
изолированный порт, и тестовый шов: HTTP endpoint с **фейковым LLM-портом**.

LLM не видит значения строк — только имена колонок и сэмплы; значения раскладывает код.
Координаты широта/долгота → `location` (PointField, SRID 4326). Отсутствующие значения
остаются пустыми; LLM не выдумывает данные.

## Acceptance criteria

- [ ] Приложение `ingestion` создано со слоями domain/application/infrastructure/interfaces и зарегистрировано.
- [ ] `POST /api/import/` принимает `.xlsx` (multipart) и работает синхронно.
- [ ] LLM-порт изолирован; реальный адаптер использует пакет `openrouter`, модель `openrouter/auto`, ключ `OPENROUTER_API_KEY`.
- [ ] LLM возвращает `{ facility_type, mapping }`; значения строк раскладываются кодом, не LLM.
- [ ] Из листа каналов создаются записи `BaseHydroFacility` + `Canal` с корректными полями.
- [ ] Координаты из файла записываются в `location`; отсутствующие значения остаются пустыми.
- [ ] Ответ содержит `{ "created": N }` с верным количеством.
- [ ] Тест: POST реальной фикстуры `.xlsx` через Django test client с фейковым LLM-портом проверяет отчёт и строки в тестовой БД (PostGIS).

## Blocked by

None - can start immediately.
