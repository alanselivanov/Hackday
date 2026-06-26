from django.core.exceptions import ValidationError
from django.db import models
from core.models import BaseHydroFacility


class SafetyCriterion(models.Model):
    """Критерии безопасности ГТС (п. 4.3.3) — предельные значения контролируемых
    показателей. Один объект может иметь несколько критериев; критерии
    пересматриваются во времени (хранится дата уточнения)."""

    # Значения совпадают с именами измеряемых полей в InspectionLog / HydroPost,
    # чтобы классификатор однозначно сопоставлял критерий с измерением.
    PARAMETER_CHOICES = [
        ('filtration_rate', 'Расход фильтрации'),
        ('deformation_value', 'Смещение/просадка'),
        ('crack_width', 'Раскрытие трещины'),
        ('water_level', 'Уровень воды'),
    ]
    # Направление опасности: растёт ли риск с увеличением показателя (трещина,
    # фильтрация — higher_worse) или с его уменьшением (мин. уровень воды — lower_worse).
    DIRECTION_HIGHER_WORSE = 'higher_worse'
    DIRECTION_LOWER_WORSE = 'lower_worse'
    DIRECTION_CHOICES = [
        (DIRECTION_HIGHER_WORSE, 'Опасность растёт с увеличением значения (K1 ≤ K2)'),
        (DIRECTION_LOWER_WORSE, 'Опасность растёт с уменьшением значения (K1 ≥ K2)'),
    ]

    facility = models.ForeignKey(BaseHydroFacility, on_delete=models.CASCADE,
        related_name="safety_criteria", verbose_name="Объект")
    parameter_name = models.CharField(max_length=30, choices=PARAMETER_CHOICES, verbose_name="Контролируемый показатель")
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default=DIRECTION_HIGHER_WORSE, verbose_name="Направление опасности")
    unit = models.CharField(max_length=30, verbose_name="Единица измерения")
    k1_warning_value = models.FloatField(verbose_name="K1 — предупреждающее значение (→ ремонт)")
    k2_critical_value = models.FloatField(verbose_name="K2 — предельное значение (→ критическое)")
    is_active = models.BooleanField(default=True, verbose_name="Действующий критерий")
    valid_from = models.DateField(verbose_name="Дата уточнения критерия (п. 4.3.3)")

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(direction='higher_worse', k1_warning_value__lte=models.F('k2_critical_value'))
                    | models.Q(direction='lower_worse', k1_warning_value__gte=models.F('k2_critical_value'))
                ),
                name='safetycriterion_k1_before_k2',
            ),
        ]

    def clean(self):
        super().clean()
        if self.k1_warning_value is None or self.k2_critical_value is None:
            return
        if self.direction == self.DIRECTION_HIGHER_WORSE and self.k1_warning_value > self.k2_critical_value:
            raise ValidationError({'k1_warning_value': 'При росте опасности с увеличением значения K1 должен быть ≤ K2.'})
        if self.direction == self.DIRECTION_LOWER_WORSE and self.k1_warning_value < self.k2_critical_value:
            raise ValidationError({'k1_warning_value': 'При росте опасности с уменьшением значения K1 должен быть ≥ K2.'})

    def __str__(self):
        return f"Критерий {self.get_parameter_name_display()} для {self.facility.name}"


class FacilityAnalytics(models.Model):
    # Соответствие группам предельных состояний по СНиП п. 5.3.2 закреплено
    # семантикой статусов (отдельное поле не вводим, обоснование — в repair_status_reason):
    #   'repair_required' ← 2-я группа (непригодность к нормальной эксплуатации:
    #                       местные дефекты, трещины, деформации);
    #   'critical'        ← 1-я группа (потеря несущей способности).
    STATUS_CHOICES = [
        ('normal', 'Норма'),
        ('inspection_required', 'Требуется осмотр'),
        ('repair_required', 'Требуется ремонт'),
        ('critical', 'Критическое состояние')
    ]
    IMPORTANCE_CHOICES = [
        ('low', 'Низкая'),
        ('medium', 'Средняя'),
        ('high', 'Высокая')
    ]
    facility = models.OneToOneField(BaseHydroFacility, on_delete=models.CASCADE, related_name="analytics", verbose_name="Объект")
    repair_status = models.CharField(max_length=30, default='normal', choices=STATUS_CHOICES, verbose_name="Статус необходимости ремонта")
    inspection_interval_days = models.IntegerField(default=365, verbose_name="Рекомендуемая частота осмотра в днях")
    next_inspection_date = models.DateField(verbose_name="Дедлайн следующего осмотра")
    calculated_importance = models.CharField(max_length=20, default='low', choices=IMPORTANCE_CHOICES, verbose_name="Класс критичности/важности объекта")
    condition_score = models.FloatField(null=True, blank=True, verbose_name="Непрерывный индекс состояния (0–100 / отношение F к R)")
    repair_status_reason = models.JSONField(null=True, blank=True, verbose_name="Обоснование статуса: сработавшие факторы (п. 4.3.3)")
    last_inspection = models.ForeignKey('monitoring.InspectionLog', on_delete=models.SET_NULL, null=True, blank=True, related_name="driven_analytics", verbose_name="Осмотр-основание текущего статуса")
    requires_verification = models.BooleanField(default=False, verbose_name="Требует проверки (нет данных / устарели / противоречивы)")
    status_changed_at = models.DateTimeField(null=True, blank=True, verbose_name="Время последней смены статуса")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время последнего расчета модели")

    def __str__(self):
        return f"Аналитика для {self.facility.name}"
