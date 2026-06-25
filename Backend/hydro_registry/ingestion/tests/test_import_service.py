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
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("наименовани", report.warnings[0].lower())

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


if __name__ == "__main__":
    unittest.main()
