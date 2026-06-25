"""Use-case импорта: оркестрация маппинга и записи распознанных листов.

Зависит только от портов (SchemaMapper, FacilityRepository), поэтому тестируется без
Django — с фейковыми реализациями. Парсинг файла выполняется выше (в interfaces) и
передаётся сюда уже как список ParsedSheet.
"""

from __future__ import annotations

from ..domain.field_catalog import SUPPORTED_FACILITY_TYPES
from ..domain.identity import find_conflicts
from ..domain.types import ImportReport, ParsedSheet
from .ports import FacilityRepository, SchemaMapper
from .row_mapper import build_records, unmapped_column_names


class ImportService:
    def __init__(self, *, mapper: SchemaMapper, repository: FacilityRepository) -> None:
        self._mapper = mapper
        self._repository = repository

    def import_sheets(self, sheets: list[ParsedSheet]) -> ImportReport:
        report = ImportReport()
        seen_unmapped: set[str] = set()

        for sheet in sheets:
            mapping_result = self._mapper.map(
                facility_hint=sheet.name, columns=sheet.columns
            )

            # Неизвестный тип от LLM не должен ронять импорт — пропускаем лист.
            if mapping_result.facility_type not in SUPPORTED_FACILITY_TYPES:
                report.warnings.append(
                    f"Лист «{sheet.name}»: неизвестный тип сооружения "
                    f"«{mapping_result.facility_type}», лист пропущен."
                )
                continue

            for name in unmapped_column_names(sheet, mapping_result):
                if name not in seen_unmapped:
                    seen_unmapped.add(name)
                    report.unmapped_columns.append(name)

            for record in build_records(sheet, mapping_result):
                # name — обязательное поле модели; без него запись бессмысленна и
                # молча сохранилась бы с пустой строкой. Пропускаем с предупреждением.
                if not record.get("name"):
                    report.warnings.append(
                        f"Лист «{sheet.name}»: строка пропущена — нет наименования."
                    )
                    continue

                facility_type = mapping_result.facility_type
                existing = self._repository.find_match(
                    facility_type=facility_type, fields=record
                )
                if existing is not None:
                    conflicts = find_conflicts(record, existing, sheet=sheet.name)
                    if conflicts:
                        # Расхождение значений — запись не пишем (ADR-0002).
                        report.conflicts.extend(conflicts)
                    else:
                        # Полное совпадение — дубль, пропускаем.
                        report.skipped_duplicates += 1
                    continue

                self._repository.create(facility_type=facility_type, fields=record)
                report.created += 1

        return report
