from django.db import models
from core.models import BaseHydroFacility


class FacilityAnalytics(models.Model):
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
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время последнего расчета модели")

    def __str__(self):
        return f"Аналитика для {self.facility.name}"
