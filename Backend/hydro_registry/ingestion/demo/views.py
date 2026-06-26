"""ВРЕМЕННАЯ демо-страница для ручного теста импорта через браузер.

Показывает по каждому загруженному сооружению: что распозналось из файла, нужен ли
ремонт (модуль 6) и когда осматривать (модуль 5) — с обоснованием обоих значений
(ADR-0004).

Демо считает ОФФЛАЙН: маппинг колонок делает HeuristicSchemaMapper напрямую (без
OpenRouter), поэтому результат детерминирован и не требует ключа/сети. Продакшен-
endpoint /api/import/ это не затрагивает.

Вся демо-обвязка лежит в папке ingestion/demo/ — чтобы удалить, снеси папку и убери
include("ingestion.demo.urls") из hydro_registry/urls.py.
"""

from __future__ import annotations

import logging
import os

from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ..application.import_service import ImportService
from ..infrastructure.llm.heuristic_mapper import HeuristicSchemaMapper
from ..infrastructure.parsers.csv_parser import CsvParser
from ..infrastructure.parsers.excel_parser import ExcelParser
from ..infrastructure.persistence.facility_repository import DjangoFacilityRepository

logger = logging.getLogger(__name__)

_EXCEL_EXTENSIONS = (".xlsx", ".xls")
_SUPPORTED_EXTENSIONS = _EXCEL_EXTENSIONS + (".csv",)

_SAMPLE_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "sample_data", "demo_facilities.csv"
)


_PAGE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Импорт сооружений — демо</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 920px; margin: 40px auto; padding: 0 16px; color: #1c1c1c; }
  h1 { font-size: 20px; }
  .card { border: 1px solid #ddd; border-radius: 10px; padding: 20px; }
  input[type=file] { display: block; margin: 14px 0; }
  button { background: #2563eb; color: #fff; border: 0; border-radius: 8px; padding: 10px 18px; font-size: 15px; cursor: pointer; }
  button:disabled { opacity: .5; cursor: default; }
  a.dl { font-size: 14px; }
  pre { background: #0f172a; color: #e2e8f0; padding: 16px; border-radius: 8px; overflow: auto; font-size: 12px; }
  .status { font-weight: 600; margin: 14px 0 6px; }
  .ok { color: #16a34a; } .err { color: #dc2626; }
  .row { display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0; }
  .pill { background: #f1f5f9; border-radius: 999px; padding: 4px 12px; font-size: 14px; }
  .note { color: #64748b; font-size: 13px; margin-top: 18px; }
  .fac { border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin: 14px 0; }
  .fac h3 { margin: 0 0 8px; font-size: 16px; }
  .fac .ftype { color: #64748b; font-weight: 400; font-size: 13px; }
  .block { margin-top: 12px; }
  .block .lbl { font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: #64748b; margin-bottom: 4px; }
  .badge { display: inline-block; border-radius: 6px; padding: 3px 10px; font-weight: 600; font-size: 14px; color: #fff; }
  .b-normal { background: #16a34a; } .b-inspection_required { background: #d97706; }
  .b-repair_required { background: #ea580c; } .b-critical { background: #dc2626; }
  .why { margin: 6px 0 0; padding-left: 18px; font-size: 14px; color: #334155; }
  .why li { margin: 2px 0; }
  .kv { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 4px 16px; font-size: 13px; }
  .kv span { color: #64748b; }
  .coef { background: #eef2ff; color: #3730a3; border-radius: 6px; padding: 2px 8px; font-size: 13px; margin: 2px; display: inline-block; }
  .coef.active { background: #c7d2fe; font-weight: 600; }
  .verify { color: #b45309; font-size: 13px; margin-top: 4px; }
</style>
</head>
<body>
  <h1>Импорт гидротехнических сооружений — демо</h1>
  <div class="card">
    <p>Выбери файл <b>.xlsx</b>, <b>.xls</b> или <b>.csv</b> и нажми «Загрузить».
       Можно скачать <a class="dl" href="/demo/import/sample.csv">пример CSV</a> со всеми кейсами
       (ремонт / норма / критическое / дубль / конфликт).</p>
    <input type="file" id="file" accept=".xlsx,.xls,.csv">
    <button id="send">Загрузить</button>
    <div id="out"></div>
  </div>
  <p class="note">Временная демо-страница (ingestion/demo/). Запрос уходит на
  <code>POST /demo/import/run/</code> и считает оффлайн (HeuristicSchemaMapper, без OpenRouter).</p>

<script>
const btn = document.getElementById('send');
const out = document.getElementById('out');

const STATUS_RU = {
  normal: 'Норма', inspection_required: 'Требуется осмотр',
  repair_required: 'Требуется ремонт', critical: 'Критическое состояние'
};

function esc(s) { return String(s).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }

function renderReason(r) {
  if (r.note) return esc(r.note);
  const parts = [];
  if (r.factor) parts.push('<b>' + esc(r.factor) + '</b>');
  if ('value' in r) parts.push('= ' + esc(r.value));
  if ('measured' in r) parts.push('измерено ' + esc(r.measured) + (r.unit ? ' ' + esc(r.unit) : ''));
  if (r.threshold) parts.push('порог ' + esc(r.threshold));
  if (r.severity) parts.push('→ ' + esc(STATUS_RU[r.severity] || r.severity));
  if (r.pressure_front_escalation) parts.push('(эскалация: напорный фронт)');
  if (r.note) parts.push(esc(r.note));
  return parts.join(' ');
}

function renderFacility(f) {
  const loaded = Object.entries(f.loaded || {})
    .map(([k, v]) => '<div><span>' + esc(k) + ':</span> ' + esc(v) + '</div>').join('');

  // Блок РЕМОНТ (модуль 6)
  let repair = '<div class="block"><div class="lbl">Нужен ли ремонт (модуль 6)</div>'
    + '<span class="badge b-' + esc(f.repair_status) + '">' + esc(f.repair_status_display) + '</span>';
  if (f.condition_score !== null && f.condition_score !== undefined)
    repair += ' <span class="pill">индекс состояния: ' + esc(f.condition_score) + '/100</span>';
  const reasons = (f.repair_reasons || []);
  if (reasons.length)
    repair += '<ul class="why">' + reasons.map(r => '<li>' + renderReason(r) + '</li>').join('') + '</ul>';
  if (f.repair_note) repair += '<div class="why">' + esc(f.repair_note) + '</div>';
  if (f.requires_verification)
    repair += '<div class="verify">⚠ требует проверки (нет данных / устарели / нет осмотра)</div>';
  repair += '</div>';

  // Блок ОСМОТР (модуль 5)
  const inf = f.inspection_factors || {};
  const factors = inf.factors || {};
  const coefs = Object.entries(factors).map(([k, v]) =>
    '<span class="coef' + (v > 1.0 ? ' active' : '') + '">' + esc(k) + ' ×' + esc(v) + '</span>').join('');
  let insp = '<div class="block"><div class="lbl">Когда осматривать (модуль 5)</div>'
    + '<span class="pill">интервал: <b>' + esc(f.inspection_interval_days) + '</b> дн</span> '
    + '<span class="pill">след. осмотр: <b>' + esc(f.next_inspection_date) + '</b></span>';
  if (inf.base_interval_days)
    insp += ' <span class="pill">база класса: ' + esc(inf.base_interval_days) + ' дн</span>';
  if (f.needs_first_inspection)
    insp += '<div class="verify">⚠ осмотров не было — нужен первичный осмотр</div>';
  if (coefs) insp += '<div class="row" style="margin-top:6px">' + coefs + '</div>';
  insp += '</div>';

  return '<div class="fac"><h3>' + esc(f.name) + ' <span class="ftype">(' + esc(f.facility_type) + ')</span></h3>'
    + '<div class="block"><div class="lbl">Что загрузилось</div><div class="kv">' + loaded + '</div></div>'
    + repair + insp + '</div>';
}

btn.addEventListener('click', async () => {
  const input = document.getElementById('file');
  if (!input.files.length) { out.innerHTML = '<div class="status err">Сначала выбери файл.</div>'; return; }
  const data = new FormData();
  data.append('file', input.files[0]);
  btn.disabled = true;
  out.innerHTML = '<div class="status">Загружаю и считаю…</div>';
  try {
    const resp = await fetch('/demo/import/run/', { method: 'POST', body: data });
    const body = await resp.json();
    const ok = resp.ok;
    let html = '<div class="status ' + (ok ? 'ok' : 'err') + '">HTTP ' + resp.status + (ok ? ' — успех' : ' — ошибка') + '</div>';
    if (ok && ('created' in body)) {
      html += '<div class="row">'
        + '<span class="pill">создано: ' + body.created + '</span>'
        + '<span class="pill">пропущено дублей: ' + body.skipped_duplicates + '</span>'
        + '<span class="pill">конфликтов: ' + (body.conflicts ? body.conflicts.length : 0) + '</span>'
        + '<span class="pill">предупреждений: ' + (body.warnings ? body.warnings.length : 0) + '</span>'
        + '<span class="pill">несопоставленных колонок: ' + (body.unmapped_columns ? body.unmapped_columns.length : 0) + '</span>'
        + '</div>';
      (body.facilities || []).forEach(f => { html += renderFacility(f); });
      if (body.conflicts && body.conflicts.length) {
        html += '<div class="block"><div class="lbl">Конфликты (не записаны)</div><ul class="why">'
          + body.conflicts.map(c => '<li>' + esc(c.key) + ' — поле <b>' + esc(c.field)
            + '</b>: было ' + esc(c.existing) + ', пришло ' + esc(c.incoming) + '</li>').join('')
          + '</ul></div>';
      }
      if (body.warnings && body.warnings.length) {
        html += '<div class="block"><div class="lbl">Предупреждения</div><ul class="why">'
          + body.warnings.map(w => '<li>' + esc(w) + '</li>').join('') + '</ul></div>';
      }
    }
    html += '<details style="margin-top:14px"><summary>Сырой JSON-ответ</summary><pre>'
      + esc(JSON.stringify(body, null, 2)) + '</pre></details>';
    out.innerHTML = html;
  } catch (e) {
    out.innerHTML = '<div class="status err">Сетевая ошибка: ' + e + '</div>';
  } finally {
    btn.disabled = false;
  }
});
</script>
</body>
</html>"""


def import_demo(request):
    return HttpResponse(_PAGE)


def sample_csv(request):
    """Отдаёт пример CSV со всеми демо-кейсами для скачивания."""
    try:
        with open(_SAMPLE_CSV_PATH, "rb") as handle:
            payload = handle.read()
    except FileNotFoundError:
        return JsonResponse({"error": "Пример CSV не найден."}, status=404)
    response = HttpResponse(payload, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="demo_facilities.csv"'
    return response


@csrf_exempt
@require_POST
def import_demo_run(request):
    """Оффлайн-импорт для демо: heuristic-маппер напрямую, без OpenRouter/ENV."""
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
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except Exception:
        return JsonResponse(
            {"error": "Не удалось прочитать файл: возможно, он повреждён или это не Excel."},
            status=400,
        )

    service = ImportService(
        mapper=HeuristicSchemaMapper(),
        repository=DjangoFacilityRepository(),
    )
    try:
        with transaction.atomic():
            report = service.import_sheets(sheets)
    except Exception:
        logger.exception("Сбой демо-импорта при обработке файла %s", upload.name)
        return JsonResponse(
            {"error": "Не удалось обработать данные. Подробности — в логах сервера."},
            status=500,
        )
    return JsonResponse(report.as_dict(), status=200)
