"""Парсер CSV: один плоский лист в тот же конвейер, что и Excel (#06).

CSV не имеет листов/merge/многоуровневой шапки — строится один RawSheet и
прогоняется через общий parse_raw_sheet. Кодировка и разделитель определяются
автоматически (госвыгрузки часто в cp1251 с разделителем «;»).
"""

from __future__ import annotations

import csv
import io
from typing import BinaryIO

from ...domain.types import ParsedSheet
from .excel_parser import parse_raw_sheet
from .excel_reader import RawSheet


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1251"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _sniff_delimiter(text: str) -> str:
    sample = text[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,\t").delimiter
    except csv.Error:
        return ";" if sample.count(";") >= sample.count(",") else ","


class CsvParser:
    def parse(self, file: BinaryIO) -> list[ParsedSheet]:
        text = _decode(file.read())
        if not text.strip():
            return [parse_raw_sheet(RawSheet("csv", [], []))]

        rows = list(csv.reader(io.StringIO(text), delimiter=_sniff_delimiter(text)))
        width = max((len(row) for row in rows), default=0)
        grid = [
            [(cell if cell != "" else None) for cell in row] + [None] * (width - len(row))
            for row in rows
        ]
        return [parse_raw_sheet(RawSheet("csv", grid, []))]
