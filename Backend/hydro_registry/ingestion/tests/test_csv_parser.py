"""Чистые тесты CSV-парсера — без Django/GDAL."""

import io
import unittest

from ingestion.infrastructure.parsers.csv_parser import CsvParser


def _upload(text: str, encoding: str = "utf-8"):
    return io.BytesIO(text.encode(encoding))


class CsvParserTests(unittest.TestCase):
    def test_semicolon_delimiter_utf8(self):
        text = "Наименование;Водоисточник;Год\nКанал А;р. Иртыш;1973\nКанал Б;р. Иртыш;1945"

        sheet = CsvParser().parse(_upload(text))[0]

        self.assertEqual([c.name for c in sheet.columns], ["Наименование", "Водоисточник", "Год"])
        self.assertEqual(len(sheet.rows), 2)
        self.assertEqual(sheet.rows[0][0], "Канал А")

    def test_comma_delimiter(self):
        text = "name,source,year\nКанал,Иртыш,1973"

        sheet = CsvParser().parse(_upload(text))[0]

        self.assertEqual([c.name for c in sheet.columns], ["name", "source", "year"])
        self.assertEqual(sheet.rows, [["Канал", "Иртыш", "1973"]])

    def test_cp1251_encoding(self):
        text = "Наименование;Водоисточник\nКанал А;р. Иртыш"

        sheet = CsvParser().parse(_upload(text, encoding="cp1251"))[0]

        self.assertEqual([c.name for c in sheet.columns], ["Наименование", "Водоисточник"])
        self.assertEqual(sheet.rows[0], ["Канал А", "р. Иртыш"])

    def test_empty_csv_yields_empty_sheet(self):
        sheet = CsvParser().parse(_upload(""))[0]

        self.assertEqual(sheet.columns, [])
        self.assertEqual(sheet.rows, [])


if __name__ == "__main__":
    unittest.main()
