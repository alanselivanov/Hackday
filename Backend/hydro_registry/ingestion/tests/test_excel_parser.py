"""Чистые тесты парсера Excel — без Django/GDAL, запускаются обычным unittest."""

import io
import unittest

from openpyxl import Workbook

from ingestion.infrastructure.parsers.excel_parser import ExcelParser


def _make_xlsx(header, rows, sheet_title="каналы"):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_title
    worksheet.append(header)
    for row in rows:
        worksheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


class ExcelParserTests(unittest.TestCase):
    def test_parses_flat_header_into_columns_and_rows(self):
        xlsx = _make_xlsx(
            ["Наименование", "Водоисточник", "Год"],
            [["Канал А", "р. Иртыш", 1973], ["Канал Б", "р. Иртыш", 1945]],
        )

        sheets = ExcelParser().parse(xlsx)

        self.assertEqual(len(sheets), 1)
        sheet = sheets[0]
        self.assertEqual(sheet.name, "каналы")
        self.assertEqual([c.name for c in sheet.columns], ["Наименование", "Водоисточник", "Год"])
        self.assertEqual(sheet.rows[0], ["Канал А", "р. Иртыш", 1973])

    def test_collects_samples_under_each_column(self):
        xlsx = _make_xlsx(
            ["Наименование", "Год"],
            [["Канал А", 1973], ["Канал Б", 1945], ["Канал В", 1928], ["Канал Г", 1955]],
        )

        sheet = ExcelParser().parse(xlsx)[0]

        year_column = sheet.columns[1]
        self.assertEqual(year_column.name, "Год")
        self.assertEqual(year_column.samples, [1973, 1945, 1928])  # максимум 3

    def test_blank_header_cells_are_skipped(self):
        xlsx = _make_xlsx(
            ["Наименование", None, "Год"],
            [["Канал А", "мусор", 1973]],
        )

        sheet = ExcelParser().parse(xlsx)[0]

        self.assertEqual([c.name for c in sheet.columns], ["Наименование", "Год"])
        self.assertEqual([c.index for c in sheet.columns], [0, 2])


if __name__ == "__main__":
    unittest.main()
