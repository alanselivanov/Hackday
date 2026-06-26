"""Чистые тесты оркестрации импорта — с фейковыми портами, без Django/GDAL."""

import unittest

from ingestion.application.import_service import ImportService
from ingestion.application.ports import FacilityRepository, SchemaMapper
from ingestion.domain.identity import IDENTITY_FIELDS
from ingestion.domain.types import ColumnSample, MappingResult, ParsedSheet


class FakeMapper(SchemaMapper):
    def __init__(self, result):
        self._result = result

    def map(self, *, facility_hint, columns):
        return self._result


class SheetAwareMapper(SchemaMapper):
    """Возвращает свою карту маппинга для каждого листа (по его имени)."""

    def __init__(self, by_sheet):
        self._by_sheet = by_sheet

    def map(self, *, facility_hint, columns):
        return self._by_sheet[facility_hint]


class FakeRepository(FacilityRepository):
    """In-memory репозиторий. Дедуп по ключу идентичности без пространственной части
    (ST_DWithin проверяется только в тесте против реального PostGIS)."""

    def __init__(self, existing=None):
        self.created = []
        self._seed = list(existing or [])

    def find_match(self, *, facility_type, fields):
        for stored_type, stored in self._seed + self.created:
            if stored_type != facility_type:
                continue
            if all(stored.get(k) == fields.get(k) for k in IDENTITY_FIELDS):
                return stored
        return None

    def create(self, *, facility_type, fields):
        self.created.append((facility_type, fields))


def _canal_sheet():
    columns = [
        ColumnSample(0, "Наименование"),
        ColumnSample(1, "Водоисточник"),
        ColumnSample(2, "Год"),
        ColumnSample(3, "Пропускная способность"),
        ColumnSample(4, "Примечание"),  # не сопоставляется
    ]
    rows = [
        ["Канал А", "р. Иртыш", 1973, 3.0, "мусор"],
        ["Канал Б", "р. Иртыш", 1945, 1.5, "мусор"],
    ]
    return ParsedSheet(name="каналы", columns=columns, rows=rows)


_MAPPING = MappingResult(
    facility_type="canal",
    mapping={0: "name", 1: "water_source", 2: "year_built", 3: "capacity"},
)


class ImportServiceTests(unittest.TestCase):
    def test_creates_one_record_per_row(self):
        repo = FakeRepository()
        service = ImportService(mapper=FakeMapper(_MAPPING), repository=repo)

        report = service.import_sheets([_canal_sheet()])

        self.assertEqual(report.created, 2)
        self.assertEqual(len(repo.created), 2)

    def test_values_are_coerced_by_field_type(self):
        repo = FakeRepository()
        service = ImportService(mapper=FakeMapper(_MAPPING), repository=repo)

        service.import_sheets([_canal_sheet()])

        facility_type, fields = repo.created[0]
        self.assertEqual(facility_type, "canal")
        self.assertEqual(fields["name"], "Канал А")
        self.assertEqual(fields["year_built"], 1973)  # int
        self.assertIsInstance(fields["year_built"], int)
        self.assertEqual(fields["capacity"], 3.0)  # float

    def test_unmapped_columns_reported_not_persisted(self):
        repo = FakeRepository()
        service = ImportService(mapper=FakeMapper(_MAPPING), repository=repo)

        report = service.import_sheets([_canal_sheet()])

        self.assertIn("Примечание", report.unmapped_columns)
        _, fields = repo.created[0]
        self.assertNotIn("Примечание", fields)

    def test_trailing_empty_rows_are_ignored(self):
        sheet = _canal_sheet()
        sheet.rows.append([None, None, None, None, None])  # хвостовая пустая строка
        sheet.rows.append(["", "", "", "", ""])
        repo = FakeRepository()
        service = ImportService(mapper=FakeMapper(_MAPPING), repository=repo)

        report = service.import_sheets([sheet])

        self.assertEqual(report.created, 2)
        self.assertEqual(len(repo.created), 2)

    def test_row_without_name_is_skipped_with_warning(self):
        sheet = _canal_sheet()
        sheet.rows.append([None, "р. Иртыш", 1960, 2.0, "мусор"])  # есть данные, нет имени
        repo = FakeRepository()
        service = ImportService(mapper=FakeMapper(_MAPPING), repository=repo)

        report = service.import_sheets([sheet])

        self.assertEqual(report.created, 2)
        self.assertTrue(any("наименовани" in w.lower() for w in report.warnings))

    def test_integral_float_strings_drop_trailing_zero(self):
        # state_act — строковое поле; число из Excel не должно стать "123.0".
        columns = [ColumnSample(0, "Наименование"), ColumnSample(1, "Гос Акт")]
        sheet = ParsedSheet(name="каналы", columns=columns, rows=[["Канал А", 123.0]])
        mapping = MappingResult(facility_type="canal", mapping={0: "name", 1: "state_act"})
        repo = FakeRepository()

        ImportService(mapper=FakeMapper(mapping), repository=repo).import_sheets([sheet])

        _, fields = repo.created[0]
        self.assertEqual(fields["state_act"], "123")


class DedupAndConflictTests(unittest.TestCase):
    def _existing_canal_a(self, **overrides):
        fields = {
            "name": "Канал А",
            "water_source": "р. Иртыш",
            "year_built": 1973,
            "capacity": 3.0,
        }
        fields.update(overrides)
        return [("canal", fields)]

    def test_full_match_is_skipped_not_created(self):
        repo = FakeRepository(existing=self._existing_canal_a())
        service = ImportService(mapper=FakeMapper(_MAPPING), repository=repo)

        report = service.import_sheets([_canal_sheet()])

        # Канал А совпал полностью → пропущен; Канал Б новый → создан.
        self.assertEqual(report.created, 1)
        self.assertEqual(report.skipped_duplicates, 1)
        self.assertEqual([f["name"] for _, f in repo.created], ["Канал Б"])

    def test_value_divergence_is_a_conflict_not_written(self):
        repo = FakeRepository(existing=self._existing_canal_a(capacity=9.9))
        service = ImportService(mapper=FakeMapper(_MAPPING), repository=repo)

        report = service.import_sheets([_canal_sheet()])

        self.assertEqual(report.created, 1)  # только Канал Б
        self.assertEqual(report.skipped_duplicates, 0)
        self.assertEqual(len(report.conflicts), 1)
        conflict = report.conflicts[0]
        self.assertEqual(conflict["field"], "capacity")
        self.assertEqual(conflict["existing"], 9.9)
        self.assertEqual(conflict["incoming"], 3.0)
        self.assertEqual(conflict["sheet"], "каналы")
        self.assertNotIn("Канал А", [f["name"] for _, f in repo.created])

    def test_no_match_creates_record(self):
        repo = FakeRepository(existing=self._existing_canal_a(name="Другой канал"))
        service = ImportService(mapper=FakeMapper(_MAPPING), repository=repo)

        report = service.import_sheets([_canal_sheet()])

        self.assertEqual(report.created, 2)
        self.assertEqual(report.skipped_duplicates, 0)
        self.assertEqual(report.conflicts, [])


class MultiSheetMergeTests(unittest.TestCase):
    """Все листы обрабатываются; одинаковые объекты на разных листах не дублируются,
    расхождения между листами уходят в conflicts с указанием листа (#04)."""

    def _sheets(self, correction_capacity):
        # Лист1: порядок колонок «имя, водоисточник, год, расход».
        list1 = ParsedSheet(
            name="Лист1",
            columns=[ColumnSample(i, n) for i, n in enumerate(("Имя", "Источник", "Год", "Расход"))],
            rows=[
                ["Канал А", "р. Иртыш", 1973, 3.0],
                ["Канал Б", "р. Иртыш", 1945, 1.5],
            ],
        )
        # Корректировка: ДРУГОЙ порядок колонок «водоисточник, имя, год, расход».
        correction = ParsedSheet(
            name="Корректировка",
            columns=[ColumnSample(i, n) for i, n in enumerate(("Источник", "Имя", "Год", "Расход"))],
            rows=[
                ["р. Иртыш", "Канал А", 1973, correction_capacity],
                ["р. Иртыш", "Канал В", 1928, 2.0],
            ],
        )
        return [list1, correction]

    def _mapper(self):
        return SheetAwareMapper(
            {
                "Лист1": MappingResult("canal", {0: "name", 1: "water_source", 2: "year_built", 3: "capacity"}),
                "Корректировка": MappingResult("canal", {0: "water_source", 1: "name", 2: "year_built", 3: "capacity"}),
            }
        )

    def test_same_facility_across_sheets_is_deduped(self):
        repo = FakeRepository()
        service = ImportService(mapper=self._mapper(), repository=repo)

        report = service.import_sheets(self._sheets(correction_capacity=3.0))

        # А и Б с Лист1, В с Корректировки; повтор А — пропущен.
        self.assertEqual(report.created, 3)
        self.assertEqual(report.skipped_duplicates, 1)
        self.assertEqual(
            sorted(f["name"] for _, f in repo.created), ["Канал А", "Канал Б", "Канал В"]
        )

    def test_cross_sheet_divergence_is_conflict_tagged_with_sheet(self):
        repo = FakeRepository()
        service = ImportService(mapper=self._mapper(), repository=repo)

        report = service.import_sheets(self._sheets(correction_capacity=9.9))

        self.assertEqual(report.created, 3)  # А, Б, В — но А не пересоздан
        self.assertEqual(report.skipped_duplicates, 0)
        self.assertEqual(len(report.conflicts), 1)
        conflict = report.conflicts[0]
        self.assertEqual(conflict["field"], "capacity")
        self.assertEqual(conflict["sheet"], "Корректировка")
        self.assertEqual([f["name"] for _, f in repo.created].count("Канал А"), 1)


class MissingKeyWarningTests(unittest.TestCase):
    """Записи без полного ключа склейки создаются, но с предупреждением (#05)."""

    def _sheet_with_coords(self, with_coords):
        columns = [ColumnSample(i, n) for i, n in enumerate(("Имя", "Источник", "Год", "Широта", "Долгота"))]
        row = ["Канал А", "р. Иртыш", 1973, 50.1, 80.2] if with_coords else ["Канал А", "р. Иртыш", 1973, None, None]
        return ParsedSheet(name="лист", columns=columns, rows=[row])

    _MAP = MappingResult(
        "canal", {0: "name", 1: "water_source", 2: "year_built", 3: "latitude", 4: "longitude"}
    )

    def test_record_without_coords_warns(self):
        repo = FakeRepository()
        report = ImportService(mapper=FakeMapper(self._MAP), repository=repo).import_sheets(
            [self._sheet_with_coords(with_coords=False)]
        )

        self.assertEqual(report.created, 1)
        self.assertTrue(any("ключа склейки" in w for w in report.warnings))

    def test_record_with_full_key_does_not_warn(self):
        repo = FakeRepository()
        report = ImportService(mapper=FakeMapper(self._MAP), repository=repo).import_sheets(
            [self._sheet_with_coords(with_coords=True)]
        )

        self.assertEqual(report.created, 1)
        self.assertEqual(report.warnings, [])


class FacilityTypeTests(unittest.TestCase):
    """Поля подклассов раскладываются для каждого типа сооружения (#07)."""

    def _run(self, facility_type, columns, mapping, row):
        sheet = ParsedSheet(
            name="лист",
            columns=[ColumnSample(i, n) for i, n in enumerate(columns)],
            rows=[row],
        )
        repo = FakeRepository()
        result = MappingResult(facility_type, mapping)
        ImportService(mapper=FakeMapper(result), repository=repo).import_sheets([sheet])
        self.assertEqual(len(repo.created), 1, repo.created)
        return repo.created[0]

    def test_sluice_subclass_fields(self):
        ftype, fields = self._run(
            "sluice",
            ["Имя", "Источник", "Год", "Затворы", "Привод"],
            {0: "name", 1: "water_source", 2: "year_built", 3: "gates_count", 4: "drive_type"},
            ["Шлюз 1", "р. Иртыш", 1980, 5, "электрический"],
        )
        self.assertEqual(ftype, "sluice")
        self.assertEqual(fields["gates_count"], 5)
        self.assertIsInstance(fields["gates_count"], int)
        self.assertEqual(fields["drive_type"], "электрический")

    def test_pumping_subclass_fields(self):
        ftype, fields = self._run(
            "pumping",
            ["Имя", "Источник", "Год", "Насосы", "Мощность"],
            {0: "name", 1: "water_source", 2: "year_built", 3: "pumps_count", 4: "installed_power"},
            ["НС-1", "р. Иртыш", 1975, 3, 250.5],
        )
        self.assertEqual(ftype, "pumping")
        self.assertEqual(fields["pumps_count"], 3)
        self.assertEqual(fields["installed_power"], 250.5)

    def test_unknown_facility_type_skips_sheet_with_warning(self):
        sheet = ParsedSheet(
            name="странный лист",
            columns=[ColumnSample(0, "Имя")],
            rows=[["Объект"]],
        )
        repo = FakeRepository()
        mapper = FakeMapper(MappingResult("teleport", {0: "name"}))
        report = ImportService(mapper=mapper, repository=repo).import_sheets([sheet])

        self.assertEqual(report.created, 0)
        self.assertEqual(repo.created, [])
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("teleport", report.warnings[0])

    def test_intake_boolean_coercion(self):
        _, fields = self._run(
            "intake",
            ["Имя", "Источник", "Год", "Самотечный"],
            {0: "name", 1: "water_source", 2: "year_built", 3: "is_gravity"},
            ["Водозабор-1", "р. Иртыш", 1990, "да"],
        )
        self.assertIs(fields["is_gravity"], True)


if __name__ == "__main__":
    unittest.main()
