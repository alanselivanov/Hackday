"""Разбор «грязного» Excel: многоуровневая объединённая шапка + отброс мусора (#02).

Шаги: прочитать сетку + merge → отметить full-width баннеры (титры, «Группа объектов»)
→ протянуть merge → найти блок шапки (до строки-нумерации колонок) → собрать флэт-имена
→ отдать данные без мусорных строк.
"""

from __future__ import annotations

from typing import Any, BinaryIO

from ...domain.types import ColumnSample, ParsedSheet
from .excel_reader import RawSheet, read_workbook

_MAX_SAMPLES = 3
_HEADER_SCAN_LIMIT = 15  # докуда искать строку-нумерацию от начала шапки
_NAME_SEPARATOR = " / "


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _is_integer_like(value: Any) -> bool:
    try:
        return float(str(value)).is_integer()
    except (ValueError, TypeError):
        return False


def _is_column_number_row(row: list[Any]) -> bool:
    """Строка-нумерация колонок (напр. 1,5,6,7…): все непустые ячейки — целые,
    их ≥4, ряд начинается с 1 и строго возрастает. Так числовые строки данных
    (напр. [1973, 5, 2]) не принимаются за нумерацию."""
    ints: list[int] = []
    for value in row:
        if _is_blank(value):
            continue
        if not _is_integer_like(value):
            return False
        ints.append(int(float(str(value))))
    if len(ints) < 4 or ints[0] != 1:
        return False
    return all(b > a for a, b in zip(ints, ints[1:]))


def _banner_rows(merged: list[tuple[int, int, int, int]], n_cols: int) -> set[int]:
    """Строки, целиком накрытые одним merge на всю ширину: титры и группы-разделители."""
    rows: set[int] = set()
    for r0, r1, c0, c1 in merged:
        if c0 == 0 and c1 >= n_cols:
            rows.update(range(r0, r1))
    return rows


def _apply_merge_fill(grid: list[list[Any]], merged: list[tuple[int, int, int, int]]) -> None:
    for r0, r1, c0, c1 in merged:
        if r0 >= len(grid) or c0 >= len(grid[r0]):
            continue
        top_left = grid[r0][c0]
        for r in range(r0, min(r1, len(grid))):
            for c in range(c0, min(c1, len(grid[r]))):
                grid[r][c] = top_left


def _flat_name(header_rows: list[list[Any]], col: int) -> str:
    parts: list[str] = []
    for row in header_rows:
        value = row[col] if col < len(row) else None
        if _is_blank(value):
            continue
        text = str(value).strip()
        if not parts or parts[-1] != text:  # схлопываем подряд идущие дубли
            parts.append(text)
    return _NAME_SEPARATOR.join(parts)


def _samples(rows: list[list[Any]], col: int) -> list[Any]:
    samples: list[Any] = []
    for row in rows:
        value = row[col] if col < len(row) else None
        if _is_blank(value):
            continue
        samples.append(value)
        if len(samples) >= _MAX_SAMPLES:
            break
    return samples


def parse_raw_sheet(raw: RawSheet) -> ParsedSheet:
    """Превратить сырой лист (сетка + merge) в ParsedSheet. Формат-нейтрально —
    используется и для Excel-листов, и для CSV (где merge просто пустой)."""
    grid = [list(row) for row in raw.grid]
    n_cols = len(grid[0]) if grid else 0
    banners = _banner_rows(raw.merged, n_cols)
    _apply_merge_fill(grid, raw.merged)

    # Начало шапки — первая непустая, не-баннерная строка.
    start = 0
    while start < len(grid) and (start in banners or all(_is_blank(v) for v in grid[start])):
        start += 1

    # Конец шапки — строка-нумерация колонок (если есть в пределах окна).
    number_row = None
    for r in range(start, min(start + _HEADER_SCAN_LIMIT, len(grid))):
        if r not in banners and _is_column_number_row(grid[r]):
            number_row = r
            break

    if number_row is not None:
        header_rows = grid[start:number_row]
        data_start = number_row + 1
    else:  # плоская шапка (одна строка) — как простой CSV/Excel
        header_rows = grid[start : start + 1]
        data_start = start + 1

    data_rows = [
        row
        for r, row in enumerate(grid[data_start:], start=data_start)
        if r not in banners and not all(_is_blank(v) for v in row)
    ]

    columns = []
    for col in range(n_cols):
        name = _flat_name(header_rows, col)
        if name:
            columns.append(ColumnSample(index=col, name=name, samples=_samples(data_rows, col)))

    return ParsedSheet(name=raw.name, columns=columns, rows=data_rows)


class ExcelParser:
    def parse(self, file: BinaryIO) -> list[ParsedSheet]:
        return [parse_raw_sheet(raw) for raw in read_workbook(file)]
