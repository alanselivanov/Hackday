"""Чистые тесты оркестрации импорта — с фейковыми портами, без Django/GDAL."""

import unittest

from ingestion.application.import_service import ImportService
from ingestion.application.ports import FacilityRepository, SchemaMapper
from ingestion.domain.types import ColumnSample, MappingResult, ParsedSheet


class FakeMapper(SchemaMapper):
    def __init__(self, result):
        self._result = result

    def map(self, *, facility_hint, columns):
        return self._result


class FakeRepository(FacilityRepository):
    def __init__(self):
        self.created = []

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


if __name__ == "__main__":
    unittest.main()
