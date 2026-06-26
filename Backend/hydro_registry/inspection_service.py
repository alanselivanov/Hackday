"""
inspection_service.py
─────────────────────
Сервисный слой: расчёт рекомендуемого периода осмотра ГТС (Задача 5).

Методология: см. «Алгоритм оценки рекомендуемого периода осмотра ГТС».
Нормативная основа: СНиП РК 3.04-01-2008, разделы 4.3.4, 5.1, 5.3.2, 5.3.7,
                     приложения 2, 7.

Принцип:
    I = I₀(K) / (k_w × k_a × k_c × k_e × k_s × k_ef)
    с ограничениями: 30 ≤ I ≤ I₀(K)

Файл кладётся, например, в  analytics/services/inspection_service.py
Зависимости из моделей:
    core.models          → BaseHydroFacility
    monitoring.models    → InspectionLog
    analytics.models     → FacilityAnalytics
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 1. КОНСТАНТЫ — все числа вынесены сюда, чтобы их было легко менять
# ═══════════════════════════════════════════════════════════════════════════

# Базовый интервал по классу, дней.
# Источник: п. 4.3.4 (потолок 5 лет) + таблица 5.1 (допустимые вероятности аварий).
# I класс  → 365 дн  (ежегодный контроль, вер. аварии ≤ 5×10⁻⁵/год)
# II класс → 730 дн  (порог «после первых двух лет» из п. 4.3.4)
# III класс→ 1095 дн (промежуточный, вер. аварии ≤ 3×10⁻³/год)
# IV класс → 1825 дн (нормативный потолок 5 лет из п. 4.3.4)
BASE_INTERVAL_BY_CLASS: dict[int, int] = {
    1: 365,
    2: 730,
    3: 1095,
    4: 1825,
}

# Расчётный срок службы по классу, лет.
# Источник: п. 5.3.7 — «не менее 100 лет для I–II класса, 50 лет для III–IV».
DESIGN_LIFE_BY_CLASS: dict[int, int] = {
    1: 100,
    2: 100,
    3: 50,
    4: 50,
}

# Абсолютный минимум интервала, дней.
# Обоснование: чаще одного раза в месяц — это уже инструментальный мониторинг
# (средства КИА по приложению 7), а не плановый выездной осмотр.
MIN_INTERVAL_DAYS: int = 30

# Месяцы повышенного сезонного риска для условий Казахстана.
# Источник: пп. 5.2.3, 5.4 — учёт паводков, ледового режима, заторно-зажорных явлений.
# Март–май — весенний паводок; ноябрь–декабрь — начало ледостава.
SEASONAL_RISK_MONTHS: frozenset[int] = frozenset({3, 4, 5, 11, 12})


# ═══════════════════════════════════════════════════════════════════════════
# 2. ДАТАКЛАСС РЕЗУЛЬТАТА
#    Одна запись содержит все выходные данные, которые нужно сохранить
#    в FacilityAnalytics и передать на фронтенд.
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class InspectionResult:
    """
    Результат расчёта для одного объекта BaseHydroFacility.

    Поля напрямую соответствуют колонкам FacilityAnalytics:
        interval_days         → inspection_interval_days
        next_inspection_date  → next_inspection_date
        factors               → repair_status_reason["inspection_factors"] (JSON)
        needs_first_inspection→ repair_status_reason["inspection_factors"]
                                ["needs_first_inspection"]  (НЕ в общий флаг
                                requires_verification — им владеет модуль 6)
    """
    # Итоговый интервал (дней) — уже ограниченный снизу и сверху.
    interval_days: int

    # Дедлайн следующего осмотра = anchor_date + interval_days.
    next_inspection_date: date

    # Базовый интервал класса (до делителя). Нужен для UI («план vs факт»).
    base_interval: int

    # Все коэффициенты с их значениями — сохраняются в repair_status_reason
    # как JSON, чтобы можно было объяснить пользователю почему именно такой срок.
    factors: dict[str, float] = field(default_factory=dict)

    # True, если объект никогда не осматривался (нет записей InspectionLog).
    # В этом случае anchor_date = сегодня, объект требует первичной проверки.
    needs_first_inspection: bool = False

    # Сообщение об ошибке, если расчёт невозможен (нет safety_class и т.д.).
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# 3. ФУНКЦИИ КОЭФФИЦИЕНТОВ
#    Каждая функция — один независимый фактор из формулы.
#    Все принимают только примитивные типы (не модели Django), поэтому
#    их легко тестировать в изоляции без базы данных.
# ═══════════════════════════════════════════════════════════════════════════

def _k_wear(wear_percentage: Optional[float]) -> float:
    """
    k_w — коэффициент физического износа.

    Источник данных: BaseHydroFacility.wear_percentage
    Нормативное обоснование: пороги привязаны к группам предельных состояний
    (п. 5.3.2). Износ ≥ 80% соответствует приближению к первой группе
    (потеря несущей способности).

    Логика: чем выше износ, тем больше k_w, тем короче итоговый интервал.
    """
    if wear_percentage is None:
        # Нет данных — принимаем нейтральный коэффициент, но в
        # InspectionResult.factors это будет видно как 1.0 (данных нет).
        return 1.0

    if wear_percentage < 30:
        return 1.0   # Нормальное состояние
    if wear_percentage < 60:
        return 1.3   # Умеренный износ
    if wear_percentage < 80:
        return 1.7   # Значительный износ
    return 2.5       # Предаварийный — близко к пред. состоянию 1-й группы


def _k_age(
    year_built: Optional[int],
    safety_class: int,
    design_service_life: Optional[int],
    today: date,
) -> float:
    """
    k_a — коэффициент возраста сооружения.

    Источники данных:
        BaseHydroFacility.year_built
        BaseHydroFacility.safety_class
        BaseHydroFacility.design_service_life (если задан явно)

    Нормативное обоснование: п. 5.3.7 — расчётный срок службы (T_d) зависит
    от класса. Возраст нормируется через α = t / T_d, а не в абсолютных годах,
    потому что 40 лет для объекта I класса (T_d=100) и для объекта IV класса
    (T_d=50) — это принципиально разный остаточный ресурс.
    """
    if year_built is None:
        return 1.0

    # Если design_service_life явно задан в БД — используем его.
    # Иначе берём нормативный по классу (п. 5.3.7).
    life = design_service_life or DESIGN_LIFE_BY_CLASS.get(safety_class, 50)

    # α — доля исчерпанного ресурса
    alpha = (today.year - year_built) / life

    if alpha < 0.5:
        return 1.0   # До половины ресурса — норма
    if alpha < 0.8:
        return 1.2   # Вторая половина ресурса
    if alpha < 1.0:
        return 1.5   # Приближение к концу срока
    return 2.0       # Расчётный срок исчерпан


def _k_condition(technical_condition: Optional[str]) -> float:
    """
    k_c — коэффициент технического состояния.

    Источник данных: BaseHydroFacility.technical_condition
    Нормативное обоснование: п. 4.3.3 — критерии безопасности как предельные
    значения показателей состояния. Неудовлетворительное состояние означает
    выход за границы нормальной эксплуатации (2-я группа пред. состояний,
    п. 5.3.2).

    Поле текстовое, поэтому нормализуем перед сравнением.
    """
    if not technical_condition:
        return 1.0

    normalized = technical_condition.strip().lower()

    # Поддерживаем разные варианты написания из реальных данных
    if any(normalized.startswith(p) for p in ("неудов", "плох", "критич", "аварий")):
        return 1.6

    return 1.0   # Удовлетворительное / хорошее / не указано


def _k_emergency(
    is_emergency_prone: bool,
    last_inspection_type: Optional[str],
) -> float:
    """
    k_e — коэффициент аварийности.

    Источники данных:
        BaseHydroFacility.is_emergency_prone
        InspectionLog.inspection_type (последняя запись)

    Нормативное обоснование: п. 4.3.4 прямо предписывает корректировку
    декларации безопасности после аварийных ситуаций. Тип осмотра
    'post_accident' в InspectionLog означает, что последний визит был
    вызван аварией — это дополнительный повышающий сигнал.
    """
    k = 1.8 if is_emergency_prone else 1.0

    # Если последний осмотр был аварийным — объект всё ещё в зоне риска
    if last_inspection_type == "post_accident":
        k = max(k, 2.0)   # Берём максимум, а не складываем — чтобы не задваивать

    return k


def _k_season(is_seasonal_risk: bool, today: date) -> float:
    """
    k_s — сезонный коэффициент.

    Источник данных: BaseHydroFacility.is_seasonal_risk
    Нормативное обоснование: пп. 5.2.3, 5.4 — требование учитывать паводки,
    ледовый режим, заторно-зажорные явления при определении нагрузок.
    Те же явления создают повышенный операционный риск для сооружений.

    Коэффициент действует ТОЛЬКО при одновременном выполнении двух условий:
    1) у объекта стоит флаг is_seasonal_risk = True;
    2) текущий месяц входит в SEASONAL_RISK_MONTHS.
    Иначе всегда 1.0.
    """
    if not is_seasonal_risk:
        return 1.0
    return 1.5 if today.month in SEASONAL_RISK_MONTHS else 1.0


def _k_efficiency(
    efficiency_project: Optional[float],
    efficiency_fact: Optional[float],
) -> float:
    """
    k_ef — коэффициент падения КПД.

    Источники данных:
        BaseHydroFacility.efficiency_project
        BaseHydroFacility.efficiency_fact

    Обоснование: расхождение проектного и фактического КПД — косвенный признак
    внутренней деградации (заиление, износ затворов, потери напора), который
    может не отражаться в формальной оценке технического состояния.
    Коэффициент вспомогательный: применяется только если оба значения заданы
    и efficiency_project > 0.

    Δef = (ef_p - ef_f) / ef_p
    """
    if not efficiency_project or efficiency_fact is None:
        return 1.0
    if efficiency_project <= 0:
        return 1.0

    delta = (efficiency_project - efficiency_fact) / efficiency_project

    if delta < 0.10:
        return 1.0    # Падение < 10% — в пределах погрешности
    if delta < 0.25:
        return 1.15   # Умеренная деградация
    return 1.30       # Значительная деградация (> 25%)


# ═══════════════════════════════════════════════════════════════════════════
# 4. ГЛАВНАЯ ФУНКЦИЯ РАСЧЁТА
#    Принимает объекты Django-моделей, возвращает InspectionResult.
#    Логика разбита на именованные шаги — каждый шаг задокументирован.
# ═══════════════════════════════════════════════════════════════════════════

def calculate_inspection_interval(
    facility,           # BaseHydroFacility — основной объект
    last_inspection,    # InspectionLog | None — последняя запись из журнала
    today: Optional[date] = None,
) -> InspectionResult:
    """
    Рассчитывает рекомендуемый интервал осмотра для одного ГТС.

    Параметры
    ─────────
    facility        — экземпляр BaseHydroFacility (или дочерней модели).
    last_inspection — последняя запись InspectionLog для этого объекта,
                      или None если осмотров не было. Получается снаружи,
                      чтобы сервис не делал свои запросы к БД
                      (принцип разделения ответственности).
    today           — дата расчёта; None → date.today(). Параметр нужен
                      для тестирования без зависимости от системного времени.

    Возвращает
    ──────────
    InspectionResult с заполненными полями.
    При ошибке возвращает InspectionResult с полем error != None
    (не бросает исключение, чтобы не ломать пакетный пересчёт).
    """
    today = today or date.today()

    # ── Шаг 1: проверка обязательного параметра ───────────────────────────
    # safety_class — единственный обязательный вход. Без него расчёт
    # по СНиП невозможен: базовый интервал I₀ не из чего определить.
    safety_class = facility.safety_class
    if safety_class not in BASE_INTERVAL_BY_CLASS:
        msg = (
            f"[{facility.name}] Не задан safety_class (1–4). "
            "Расчёт по СНиП РК 3.04-01-2008 невозможен."
        )
        logger.warning(msg)
        return InspectionResult(
            interval_days=BASE_INTERVAL_BY_CLASS[4],  # консервативный fallback
            next_inspection_date=today + timedelta(days=BASE_INTERVAL_BY_CLASS[4]),
            base_interval=BASE_INTERVAL_BY_CLASS[4],
            error=msg,
            needs_first_inspection=True,
        )

    # ── Шаг 2: базовый интервал I₀ по классу ─────────────────────────────
    # Источник: п. 4.3.4 (потолок 5 лет) + таблица 5.1.
    base = BASE_INTERVAL_BY_CLASS[safety_class]

    # ── Шаг 3: извлечение данных для коэффициентов из модели ─────────────
    # Извлекаем все нужные поля в локальные переменные — это делает
    # вызовы функций коэффициентов читаемыми и упрощает мокирование в тестах.

    wear_pct        = getattr(facility, "wear_percentage", None)
    year_built      = getattr(facility, "year_built", None)
    design_life     = getattr(facility, "design_service_life", None)
    tech_condition  = getattr(facility, "technical_condition", None)
    is_emergency    = getattr(facility, "is_emergency_prone", False)
    is_seasonal     = getattr(facility, "is_seasonal_risk", False)
    eff_project     = getattr(facility, "efficiency_project", None)
    eff_fact        = getattr(facility, "efficiency_fact", None)

    # Тип последнего осмотра — нужен для k_e.
    # InspectionLog.inspection_type: 'planned', 'post_accident', 'post_repair',
    # 'commissioning' (из INSPECTION_TYPE_CHOICES).
    last_type = getattr(last_inspection, "inspection_type", None) if last_inspection else None

    # ── Шаг 4: расчёт всех коэффициентов ─────────────────────────────────
    # Каждый коэффициент ≥ 1.0. Чем хуже фактор — тем больше коэффициент
    # и тем сильнее сокращается итоговый интервал.
    factors = {
        # k_w: износ из BaseHydroFacility.wear_percentage
        "k_wear":       _k_wear(wear_pct),

        # k_a: нормированный возраст (year_built / design_service_life или по классу)
        "k_age":        _k_age(year_built, safety_class, design_life, today),

        # k_c: техническое состояние из BaseHydroFacility.technical_condition
        "k_condition":  _k_condition(tech_condition),

        # k_e: аварийность (is_emergency_prone) + тип последнего осмотра
        "k_emergency":  _k_emergency(is_emergency, last_type),

        # k_s: сезонный риск (is_seasonal_risk) + текущий месяц
        "k_season":     _k_season(is_seasonal, today),

        # k_ef: падение КПД (efficiency_project / efficiency_fact)
        "k_efficiency": _k_efficiency(eff_project, eff_fact),
    }

    # ── Шаг 5: применение формулы ─────────────────────────────────────────
    # I = I₀ / (k_w × k_a × k_c × k_e × k_s × k_ef)
    # Используем мультипликативную схему (деление), а не аддитивную (сумму баллов),
    # потому что факторы действуют независимо: каждый должен уметь сократить
    # интервал самостоятельно, без «компенсации» другими факторами.
    divisor = 1.0
    for v in factors.values():
        divisor *= v

    raw_interval = base / divisor

    # ── Шаг 6: ограничители ───────────────────────────────────────────────
    # Снизу (30 дней): чаще — это инструментальный мониторинг, не осмотр (прил. 7).
    # Сверху (base): факторы могут только сокращать интервал, не удлинять его
    # сверх нормативного потолка класса.
    interval = max(MIN_INTERVAL_DAYS, min(round(raw_interval), base))

    # ── Шаг 7: точка отсчёта и дата следующего осмотра ───────────────────
    # D_next = D_last + I
    # D_last берётся из InspectionLog.inspection_date последней записи.
    # Если записей нет — объект никогда не осматривался, нужен первичный осмотр.
    if last_inspection and getattr(last_inspection, "inspection_date", None):
        anchor = last_inspection.inspection_date
        needs_first = False
    else:
        # Нет истории: отсчёт от сегодня, флаг первичного осмотра.
        # Это попадёт в FacilityAnalytics.requires_verification = True.
        anchor = today
        needs_first = True
        logger.info(
            "[%s] Нет записей InspectionLog — требуется первичный осмотр.",
            facility.name,
        )

    next_date = anchor + timedelta(days=interval)

    return InspectionResult(
        interval_days=interval,
        next_inspection_date=next_date,
        base_interval=base,
        factors=factors,
        needs_first_inspection=needs_first,
    )


# ═══════════════════════════════════════════════════════════════════════════
# 5. ФУНКЦИЯ СОХРАНЕНИЯ В FacilityAnalytics
#    Отдельная функция — чтобы логика расчёта и запись в БД были независимы.
#    Это позволяет вызывать calculate_inspection_interval() в тестах без БД.
# ═══════════════════════════════════════════════════════════════════════════

def save_inspection_result(analytics, result: InspectionResult) -> None:
    """
    Записывает InspectionResult в существующий объект FacilityAnalytics.

    Параметры
    ─────────
    analytics — экземпляр FacilityAnalytics (уже загруженный из БД).
    result    — InspectionResult от calculate_inspection_interval().

    РАЗГРАНИЧЕНИЕ ОТВЕТСТВЕННОСТИ С МОДУЛЕМ 6 (analytics/services.py)
    ───────────────────────────────────────────────────────────────
    Чтобы два алгоритма не затирали поля друг друга, у каждого свой набор колонок:

        Модуль 5 (этот файл) ВЛАДЕЕТ:
            • inspection_interval_days
            • next_inspection_date
            • repair_status_reason["inspection_factors"]   ← только этот ключ

        Модуль 6 (recalculate_status) ВЛАДЕЕТ:
            • repair_status, condition_score, last_inspection, status_changed_at
            • requires_verification                        ← единый владелец
            • repair_status_reason["factors"]              ← только этот ключ

    Поэтому здесь:
      1) пишем repair_status_reason ЧЕРЕЗ СЛИЯНИЕ — трогаем только свой ключ
         "inspection_factors", ключ "factors" модуля 6 не затираем;
      2) НЕ трогаем requires_verification — это поле принадлежит модулю 6
         (он богаче: учитывает просрочку, отсутствие измерений, противоречия,
         и сам выставляет флаг, когда осмотров нет). Признак «нужен первичный
         осмотр» и ошибку расчёта мы кладём внутрь JSON "inspection_factors",
         а не в общий флаг — так модули не конфликтуют за одну колонку.

    save() идёт с update_fields, поэтому строго ограничен нашими колонками —
    параллельный вызов модуля 6 на том же объекте ничего из его полей не теряет.
    """
    analytics.inspection_interval_days = result.interval_days
    analytics.next_inspection_date = result.next_inspection_date

    # Сливаем repair_status_reason: читаем актуальный словарь и обновляем
    # ТОЛЬКО свой ключ "inspection_factors". Ключ "factors" (модуль 6) остаётся.
    existing_reason = analytics.repair_status_reason or {}
    if not isinstance(existing_reason, dict):
        existing_reason = {}
    existing_reason["inspection_factors"] = {
        "base_interval_days": result.base_interval,
        "computed_interval_days": result.interval_days,
        "factors": {k: round(v, 3) for k, v in result.factors.items()},
        "needs_first_inspection": result.needs_first_inspection,
        **({"error": result.error} if result.error else {}),
    }
    analytics.repair_status_reason = existing_reason

    analytics.save(update_fields=[
        "inspection_interval_days",
        "next_inspection_date",
        "repair_status_reason",
        "updated_at",
    ])


# ═══════════════════════════════════════════════════════════════════════════
# 6. ОРКЕСТРАТОР: пересчёт одного объекта целиком
#    Объединяет: загрузку данных → расчёт → сохранение.
#    Вызывается из Django management command, Celery task или сигнала.
# ═══════════════════════════════════════════════════════════════════════════

def run_for_facility(facility, today: Optional[date] = None) -> InspectionResult:
    """
    Полный цикл для одного объекта:
        1. Загрузить последний InspectionLog.
        2. Рассчитать интервал.
        3. Сохранить в FacilityAnalytics.

    Параметры
    ─────────
    facility — экземпляр BaseHydroFacility.
    today    — дата расчёта (None → сегодня).

    Почему загружаем InspectionLog здесь, а не внутри calculate?
    Чтобы calculate_inspection_interval() оставался чистой функцией без
    обращений к БД — её можно вызывать в тестах с мок-объектами.
    """
    # Ленивый импорт Django-моделей: если функцию вызывают в тестах
    # без реальной БД, импорт не ломает тест.
    from monitoring.models import InspectionLog
    from analytics.models import FacilityAnalytics

    # Последний осмотр — сортируем по дате, берём первый.
    last_inspection = (
        InspectionLog.objects
        .filter(facility=facility)
        .order_by("-inspection_date")
        .first()
    )

    result = calculate_inspection_interval(facility, last_inspection, today)

    # get_or_create: если FacilityAnalytics ещё нет для этого объекта —
    # создаём с минимальными дефолтами, потом save_inspection_result допишет.
    analytics, created = FacilityAnalytics.objects.get_or_create(
        facility=facility,
        defaults={
            "next_inspection_date": result.next_inspection_date,
            "repair_status": "normal",
        },
    )
    if created:
        logger.info("[%s] Создан новый FacilityAnalytics.", facility.name)

    save_inspection_result(analytics, result)

    logger.info(
        "[%s] Интервал=%d дн, след.осмотр=%s, нужен_первый=%s",
        facility.name,
        result.interval_days,
        result.next_inspection_date,
        result.needs_first_inspection,
    )
    return result


def run_for_all(today: Optional[date] = None) -> dict:
    """
    Пакетный пересчёт всех объектов BaseHydroFacility.
    Используется в ночном Celery-task или management command.

    Возвращает краткую статистику: {'total': N, 'errors': M}.
    """
    from core.models import BaseHydroFacility

    facilities = BaseHydroFacility.objects.select_related("analytics").all()
    total, errors = 0, 0

    for facility in facilities:
        try:
            result = run_for_facility(facility, today)
            if result.error:
                errors += 1
        except Exception as exc:
            logger.exception("[%s] Ошибка при расчёте: %s", facility.name, exc)
            errors += 1
        total += 1

    logger.info("Пересчёт завершён: total=%d, errors=%d", total, errors)
    return {"total": total, "errors": errors}
