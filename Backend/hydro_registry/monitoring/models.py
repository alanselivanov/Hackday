from django.db import models
from core.models import BaseHydroFacility


class HydroPost(BaseHydroFacility):
    post_type = models.CharField(max_length=50, verbose_name="Тип поста (Автоматический / Ручной)")
    equipment_installed = models.CharField(max_length=255, null=True, blank=True, verbose_name="Модель датчика/эхолота")
    current_water_level = models.FloatField(null=True, blank=True, verbose_name="Текущий уровень воды, см")
    critical_water_level = models.FloatField(null=True, blank=True, verbose_name="Критический уровень для оповещения, см")
    last_telemetry_at = models.DateTimeField(null=True, blank=True, verbose_name="Время последнего пинга от поста")


class InspectionLog(models.Model):
    CRACK_CHOICES = [
        (0, 'Нет'),
        (1, 'Микротрещины'),
        (2, 'Средние дефекты'),
        (3, 'Сквозные/Критические трещины')
    ]
    facility = models.ForeignKey(BaseHydroFacility, on_delete=models.CASCADE, related_name="inspection_logs", verbose_name="Объект")
    inspection_date = models.DateField(verbose_name="Дата проведения осмотра")
    inspector_name = models.CharField(max_length=255, verbose_name="ФИО инспектора")
    has_cracks = models.BooleanField(default=False, verbose_name="Наличие трещин/разрушений бетона")
    crack_criticality = models.IntegerField(default=0, choices=CRACK_CHOICES, verbose_name="Тяжесть трещин")
    is_silted = models.BooleanField(default=False, verbose_name="Заилено/заращено ли русло")
    siltation_percentage = models.FloatField(default=0.0, verbose_name="Процент заиления русла (0.0 - 100.0)")
    has_filtration = models.BooleanField(default=False, verbose_name="Наличие опасной фильтрации/утечки воды")
    has_deformation = models.BooleanField(default=False, verbose_name="Наличие просадок, сдвигов плит, пучения грунта")
    equipment_malfunction = models.BooleanField(default=False, verbose_name="Поломка затворов/насосов/механической части")
    detected_wear_override = models.FloatField(null=True, blank=True, verbose_name="Фактический износ, зафиксированный на месте, %")

    def __str__(self):
        return f"Осмотр {self.facility.name} от {self.inspection_date}"
