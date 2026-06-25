"""HTTP-вход импорта. Синхронный, без аутентификации (ADR-0003, хакатон).

Канонический тестовый шов фичи: POST файла сюда, мокается только LLM-порт.
"""

from __future__ import annotations

import logging
import os

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ..application.import_service import ImportService
from ..infrastructure.llm.factory import resolve_schema_mapper
from ..infrastructure.parsers.csv_parser import CsvParser
from ..infrastructure.parsers.excel_parser import ExcelParser
from ..infrastructure.persistence.facility_repository import DjangoFacilityRepository

logger = logging.getLogger(__name__)

_EXCEL_EXTENSIONS = (".xlsx", ".xls")
_SUPPORTED_EXTENSIONS = _EXCEL_EXTENSIONS + (".csv",)


@csrf_exempt
@require_POST
def import_facilities(request):
    upload = request.FILES.get("file")
    if upload is None:
        return JsonResponse({"error": "Файл не передан (поле 'file')."}, status=400)

    extension = os.path.splitext(upload.name)[1].lower()
    if extension not in _SUPPORTED_EXTENSIONS:
        return JsonResponse(
            {"error": f"Формат {extension or '?'} не поддерживается. Ожидается .xlsx, .xls или .csv."},
            status=400,
        )

    parser = CsvParser() if extension == ".csv" else ExcelParser()
    try:
        sheets = parser.parse(upload)
    except ValueError as error:  # неизвестная сигнатура файла
        return JsonResponse({"error": str(error)}, status=400)
    except Exception:  # повреждённый/нечитаемый файл (BadZipFile, XLRDError, …)
        return JsonResponse(
            {"error": "Не удалось прочитать файл: возможно, он повреждён или это не Excel."},
            status=400,
        )

    service = ImportService(
        mapper=resolve_schema_mapper(),
        repository=DjangoFacilityRepository(),
    )
    # Атомарно: при сбое на любой строке частичная запись откатывается.
    # Ошибку LLM/БД отдаём как JSON (а не HTML-500), трейс — в лог сервера.
    try:
        with transaction.atomic():
            report = service.import_sheets(sheets)
    except Exception:
        logger.exception("Сбой импорта при обработке файла %s", upload.name)
        return JsonResponse(
            {"error": "Не удалось обработать данные (возможно, недоступен LLM-сервис "
                      "OpenRouter). Подробности — в логах сервера."},
            status=502,
        )
    return JsonResponse(report.as_dict(), status=200)
