"""ВРЕМЕННАЯ демо-страница для ручного теста импорта через браузер.

Вся демо-обвязка лежит в папке ingestion/demo/ — чтобы удалить, снеси папку и
убери include("ingestion.demo.urls") из hydro_registry/urls.py.
"""

from __future__ import annotations

from django.http import HttpResponse

_PAGE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Импорт сооружений — демо</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 760px; margin: 40px auto; padding: 0 16px; color: #1c1c1c; }
  h1 { font-size: 20px; }
  .card { border: 1px solid #ddd; border-radius: 10px; padding: 20px; }
  input[type=file] { display: block; margin: 14px 0; }
  button { background: #2563eb; color: #fff; border: 0; border-radius: 8px; padding: 10px 18px; font-size: 15px; cursor: pointer; }
  button:disabled { opacity: .5; cursor: default; }
  pre { background: #0f172a; color: #e2e8f0; padding: 16px; border-radius: 8px; overflow: auto; }
  .status { font-weight: 600; margin: 14px 0 6px; }
  .ok { color: #16a34a; } .err { color: #dc2626; }
  .row { display: flex; gap: 18px; flex-wrap: wrap; margin: 10px 0; }
  .pill { background: #f1f5f9; border-radius: 999px; padding: 4px 12px; font-size: 14px; }
  .note { color: #64748b; font-size: 13px; margin-top: 18px; }
</style>
</head>
<body>
  <h1>Импорт гидротехнических сооружений — демо</h1>
  <div class="card">
    <p>Выбери файл <b>.xlsx</b>, <b>.xls</b> или <b>.csv</b> и нажми «Загрузить».</p>
    <input type="file" id="file" accept=".xlsx,.xls,.csv">
    <button id="send">Загрузить</button>
    <div id="out"></div>
  </div>
  <p class="note">Это временная демо-страница (ingestion/demo/). Запрос уходит на
  <code>POST /api/import/</code> и реально дёргает OpenRouter для разбора колонок.</p>

<script>
const btn = document.getElementById('send');
const out = document.getElementById('out');

btn.addEventListener('click', async () => {
  const input = document.getElementById('file');
  if (!input.files.length) { out.innerHTML = '<div class="status err">Сначала выбери файл.</div>'; return; }

  const data = new FormData();
  data.append('file', input.files[0]);

  btn.disabled = true;
  out.innerHTML = '<div class="status">Загружаю и разбираю…</div>';
  try {
    const resp = await fetch('/api/import/', { method: 'POST', body: data });
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
    }
    html += '<pre>' + JSON.stringify(body, null, 2) + '</pre>';
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
