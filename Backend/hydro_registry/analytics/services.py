"""
Модуль 6 — присвоение статуса ГТС: норма / требуется осмотр / требуется ремонт /
критическое состояние.

Опорные положения СНиП РК 3.04-01-2008:
  - п. 4.3.3 — критерии безопасности (предельные значения показателей) → SafetyCriterion (K1/K2);
  - п. 5.3.2 — две группы предельных состояний:
        2-я группа (непригодность к нормальной эксплуатации) → 'repair_required',
        1-я группа (потеря несущей способности)            → 'critical';
  - п. 4.3.4 — корректировка после аварийных ситуаций → учёт inspection_type='post_accident';
  - п. 5.1.3 / 5.3.7 — напорный фронт: серьёзный дефект на нём тяжелее (эскалация).

ФОРМА АЛГОРИТМА:
  статус = SEVERITY_LEVELS[ max(severity по всем источникам доказательств) ]
  где каждый источник (критерий K1/K2, признак осмотра, контекст объекта) даёт severity 0..3,
  а итоговый статус определяется ХУДШИМ фактором.

Размещено в analytics/services.py (логика классификации вынесена из models.py).
Вызывайте recalculate_status(analytics) после каждого нового InspectionLog и после
пересчёта модуля 5. Для удобного analytics.recalculate() метод навешивается в
AnalyticsConfig.ready() (см. analytics/apps.py).
"""

from django.utils import timezone


def _merge_reason(analytics, new_reason):
    """Сливает обоснование статуса в repair_status_reason, НЕ затирая раздел
    модуля 5 (расчёт периода осмотра, inspection_service.py).

    Поле repair_status_reason общее для двух алгоритмов:
        ключ "factors"            — владеет этот модуль (статус ремонта);
        ключ "inspection_factors" — владеет модуль 5 (период осмотра).
    Модуль 5 пишет свой ключ через слияние; здесь мы делаем то же со своим,
    чтобы при пересчёте статуса не потерять уже посчитанный период осмотра."""
    existing = analytics.repair_status_reason
    preserved = {}
    if isinstance(existing, dict) and "inspection_factors" in existing:
        preserved["inspection_factors"] = existing["inspection_factors"]

    if new_reason:
        return {**preserved, **new_reason}
    # Своих факторов нет: сохраняем только чужой раздел, иначе None.
    return preserved or None


# Лестница тяжести: индекс ↔ FacilityAnalytics.STATUS_CHOICES
SEVERITY_LEVELS = {
    0: 'normal',               # норма
    1: 'inspection_required',  # требуется осмотр
    2: 'repair_required',      # требуется ремонт  (2-я группа предельных состояний)
    3: 'critical',             # критическое       (1-я группа предельных состояний)
}

# Признаки, относящиеся к несущей способности / напорному фронту.
# Для объектов с has_pressure_front=True их severity≥2 эскалируется до 3 (1-я группа).
STRUCTURAL_FACTORS = {'has_filtration', 'has_deformation', 'crack_criticality'}


def _get_measured_value(facility, inspection, parameter_name):
    """Сопоставляет SafetyCriterion.parameter_name с конкретным измерением.
    Значения choices совпадают с именами полей моделей, поэтому берём их напрямую."""
    if parameter_name == 'water_level':
        # уровень воды живёт на HydroPost, а не в InspectionLog
        if facility.facility_type != 'post':
            return None
        try:
            return facility.hydropost.current_water_level
        except Exception:
            return None
    # filtration_rate / deformation_value / crack_width — поля InspectionLog
    return getattr(inspection, parameter_name, None)


def _evaluate_criterion(criterion, value):
    """Оценка одного активного критерия безопасности.
    Возвращает (severity, ratio):
      severity — 0 норма / 2 достигнут K1 (ремонт) / 3 достигнут K2 (критическое);
      ratio    — доля приближения к K2 в [0..], для condition_score.
    None — измерения нет (обработается как requires_verification)."""
    if value is None:
        return None

    k1 = criterion.k1_warning_value
    k2 = criterion.k2_critical_value

    if criterion.direction == criterion.DIRECTION_HIGHER_WORSE:
        ratio = (value / k2) if k2 else 0.0
        if value >= k2:
            return 3, ratio
        if value >= k1:
            return 2, ratio
        return 0, ratio
    else:  # DIRECTION_LOWER_WORSE — опасно понижение
        ratio = (k2 / value) if value else 2.0
        if value <= k2:
            return 3, ratio
        if value <= k1:
            return 2, ratio
        return 0, ratio


def _evaluate_inspection_flags(facility, inspection):
    """Качественные признаки осмотра — для объектов без КИА / без числовых критериев.
    Возвращает список (severity, reason_dict).

    Числовые пороги ниже (50% заиления, 60/80% износа) — единственные значения,
    взятые не из полей моделей, а назначенные как разумные значения по умолчанию.
    Их стоит вынести в настройки/согласовать с нормами при появлении реальных данных."""
    factors = []

    # Трещины: crack_criticality 0..3 → severity 0/1/2/3
    crack_map = {1: 1, 2: 2, 3: 3}
    if inspection.crack_criticality in crack_map:
        factors.append((crack_map[inspection.crack_criticality], {
            'factor': 'crack_criticality',
            'value': inspection.get_crack_criticality_display(),
        }))

    # Опасная фильтрация без измерения → 2-я группа (ремонт)
    if inspection.has_filtration and inspection.filtration_rate is None:
        factors.append((2, {'factor': 'has_filtration', 'value': True}))

    # Деформации без измерения → 2-я группа (ремонт)
    if inspection.has_deformation and inspection.deformation_value is None:
        factors.append((2, {'factor': 'has_deformation', 'value': True}))

    # Поломка механической части → непригодность к нормальной эксплуатации (ремонт)
    if inspection.equipment_malfunction:
        factors.append((2, {'factor': 'equipment_malfunction', 'value': True}))

    # Заиление русла: снижение пропускной способности
    if inspection.siltation_percentage >= 50:
        factors.append((2, {'factor': 'siltation_percentage', 'value': inspection.siltation_percentage}))
    elif inspection.is_silted or inspection.siltation_percentage > 0:
        factors.append((1, {'factor': 'siltation_percentage', 'value': inspection.siltation_percentage}))

    # Износ: фактический с места (detected_wear_override) приоритетнее паспортного
    wear = inspection.detected_wear_override
    if wear is None:
        wear = facility.wear_percentage
    if wear is not None:
        if wear >= 80:
            factors.append((2, {'factor': 'wear_percentage', 'value': wear}))
        elif wear >= 60:
            factors.append((1, {'factor': 'wear_percentage', 'value': wear}))

    return factors


def recalculate_status(analytics):
    """Главная функция модуля 6. Принимает FacilityAnalytics, пересчитывает
    repair_status / condition_score / repair_status_reason / requires_verification
    / last_inspection / status_changed_at и сохраняет объект.

    Доступна как analytics.recalculate() (метод навешен в AnalyticsConfig.ready())."""
    facility = analytics.facility
    today = timezone.localdate()

    reasons = []
    severities = []
    ratios = []
    needs_verification = False

    # 1. Берём последний осмотр как основание статуса
    inspection = (facility.inspection_logs
                  .order_by('-inspection_date', '-id')
                  .first())

    # 1a. Осмотров нет — оценить нельзя
    if inspection is None:
        analytics.last_inspection = None
        analytics.repair_status = 'normal'
        analytics.condition_score = None
        analytics.requires_verification = True
        analytics.repair_status_reason = _merge_reason(
            analytics, {'note': 'Нет ни одного осмотра — статус не рассчитан'})
        analytics.save()
        return analytics

    analytics.last_inspection = inspection

    # 2. Количественные критерии безопасности (п. 4.3.3): сравнение с K1/K2
    for criterion in facility.safety_criteria.filter(is_active=True):
        value = _get_measured_value(facility, inspection, criterion.parameter_name)
        result = _evaluate_criterion(criterion, value)

        if result is None:
            # критерий действует, но измерения нет → данные неполны
            needs_verification = True
            reasons.append({'factor': criterion.parameter_name,
                            'note': 'активный критерий без измерения'})
            continue

        sev, ratio = result
        ratios.append(min(ratio, 1.0))
        if sev > 0:
            severities.append(sev)
            reasons.append({
                'factor': criterion.parameter_name,
                'measured': value,
                'unit': criterion.unit,
                'threshold': 'K2' if sev == 3 else 'K1',
                'k1': criterion.k1_warning_value,
                'k2': criterion.k2_critical_value,
                'severity': SEVERITY_LEVELS[sev],
            })

    # 3. Качественные признаки осмотра (+ эскалация для напорного фронта)
    for sev, reason in _evaluate_inspection_flags(facility, inspection):
        if (facility.has_pressure_front and sev >= 2
                and reason['factor'] in STRUCTURAL_FACTORS):
            sev = 3  # СНиП 5.1.3/5.3.7: разрушение элемента напорного фронта → 1-я группа
            reason['pressure_front_escalation'] = True
        severities.append(sev)
        reasons.append(reason)

    # 4. Контекст объекта — только поднимает «пол», не понижает статус
    if facility.is_emergency_prone:
        severities.append(1)
        reasons.append({'factor': 'is_emergency_prone', 'value': True})

    if inspection.inspection_type == 'post_accident':
        severities.append(1)  # п. 4.3.4 — после аварии минимум «требуется осмотр»
        reasons.append({'factor': 'inspection_type', 'value': 'post_accident'})

    # 5. Свежесть данных: просрочен дедлайн осмотра из модуля 5
    if analytics.next_inspection_date and analytics.next_inspection_date < today:
        needs_verification = True
        reasons.append({'factor': 'next_inspection_date',
                        'note': 'дедлайн осмотра просрочен — данные устарели'})

    # 6. Итоговый статус — ХУДШИЙ фактор
    final_severity = max(severities) if severities else 0
    new_status = SEVERITY_LEVELS[final_severity]

    # 7. Непрерывный индекс состояния (0..100, выше = здоровее)
    quant_damage = (max(ratios) * 100) if ratios else 0.0
    qual_damage = (final_severity / 3.0) * 100
    analytics.condition_score = round(max(0.0, 100.0 - max(quant_damage, qual_damage)), 1)

    # 8. Фиксация момента смены статуса
    if new_status != analytics.repair_status:
        analytics.status_changed_at = timezone.now()
    analytics.repair_status = new_status

    analytics.requires_verification = needs_verification
    analytics.repair_status_reason = _merge_reason(
        analytics, {'factors': reasons} if reasons else None)
    analytics.save()
    return analytics
