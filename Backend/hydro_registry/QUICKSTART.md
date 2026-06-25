
## 1. Установить PostgreSQL + PostGIS (Windows)

### PostGIS

PostGIS **не входит** в базовую установку PostgreSQL — нужен отдельный шаг.

1. https://download.osgeo.org/postgis/windows/pg16/ (для PG 16).
2. Скачать `postgis-bundle-pg16x64-setup-*.exe`.
3. Запустить **от имени администратора**.
4. Путь к PostgreSQL: `C:\Program Files\PostgreSQL\16`.

### Создать базу

В pgAdmin: правый клик на **Databases → hydro_registry** (или создать новую БД), открыть **Query Tool** на этой базе:

```sql
CREATE EXTENSION postgis;
```

Проверка:

```sql
SELECT PostGIS_Version();
```

---

## 2. Клонировать репозиторий

```bash
git clone <url-репозитория>
cd Hackday/hydro_registry
```

---

## 3. Python и зависимости

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 4. Настроить `.env`

Скопировать шаблон и заполнить:

```bash
cp .env.example .env
```

```env
DB_NAME=hydro_registry
DB_USER=postgres
DB_PASSWORD=ваш_пароль
DB_HOST=localhost
DB_PORT=5432
```

Файл `.env` не коммитится в git.

---

## 5. Миграции

```bash
python manage.py check
python manage.py migrate
```

`makemigrations` уже выполнен — миграции лежат в `*/migrations/`. Запускать снова только если вы меняли модели:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 6. Суперпользователь (для админки)

```bash
python manage.py createsuperuser
```

---

## 7. Запуск сервера

```bash
python manage.py runserver
```

Открыть:

- http://127.0.0.1:8000/admin/

---

## Частые ошибки

| Ошибка | Решение |
|--------|---------|
| `Could not find the GDAL library` | Установить PostGIS bundle или OSGeo4W; указать `GDAL_LIBRARY_PATH` в `.env` |
| `расширение "postgis" отсутствует` | Установить PostGIS в PostgreSQL (см. шаг 1), затем `CREATE EXTENSION postgis;` |
| `password authentication failed` | Проверить `DB_PASSWORD` в `.env` |
| `database "hydro_registry" does not exist` | Создать БД в pgAdmin или `CREATE DATABASE hydro_registry;` |
| `CREATE EXTENSION` в pgAdmin с `\c` | `\c` — команда `psql`, в Query Tool не работает. Открыть Query Tool **на базе hydro_registry** |

---

## Структура проекта

```
hydro_registry/
├── manage.py
├── requirements.txt
├── .env.example          # шаблон переменных окружения
├── core/                 # BaseHydroFacility
├── infrastructure/       # каналы, шлюзы, водозаборы...
├── monitoring/           # гидропосты, журнал осмотров
├── analytics/            # аналитика объектов
└── hydro_registry/       # settings, urls, wsgi
```

## Полезные команды

```bash
python manage.py check          # проверка конфигурации
python manage.py showmigrations # статус миграций
python manage.py dbshell        # консоль PostgreSQL
```
