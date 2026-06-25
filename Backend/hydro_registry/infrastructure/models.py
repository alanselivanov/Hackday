from django.db import models
from core.models import BaseHydroFacility


class Canal(BaseHydroFacility):
    capacity = models.FloatField(null=True, blank=True, verbose_name="Пропускная способность, м3/с")
    total_length = models.FloatField(null=True, blank=True, verbose_name="Всего протяжённость, км")
    earth_length = models.FloatField(null=True, blank=True, verbose_name="Земляное русло, км")
    lined_length = models.FloatField(null=True, blank=True, verbose_name="Облицованное русло, км")
    area_regular = models.FloatField(default=0.0, verbose_name="Подвешенная площадь: регулярное орошение, га")
    area_liman = models.FloatField(default=0.0, verbose_name="Лиманное орошение, га")
    area_flooded = models.FloatField(default=0.0, verbose_name="Обводненное, га")
    bottom_width = models.FloatField(null=True, blank=True, verbose_name="Ширина по дну, м")
    top_width = models.FloatField(null=True, blank=True, verbose_name="Ширина по верху, м")
    depth = models.FloatField(null=True, blank=True, verbose_name="Глубина, м")


class Sluice(BaseHydroFacility):
    gates_count = models.IntegerField(null=True, blank=True, verbose_name="Количество затворов/сооружений")
    gate_type = models.CharField(max_length=100, null=True, blank=True, verbose_name="Тип затвора")
    drive_type = models.CharField(max_length=100, null=True, blank=True, verbose_name="Привод затвора (электрический, механический, ручной)")
    max_discharge = models.FloatField(null=True, blank=True, verbose_name="Максимальный сброс воды, м3/с")


class WaterIntake(BaseHydroFacility):
    intake_type = models.CharField(max_length=100, verbose_name="Тип водозабора (Береговой, русловой, плавучий)")
    is_gravity = models.BooleanField(default=True, verbose_name="Самотечный (True) или механический (False)")
    fish_protection = models.BooleanField(default=False, verbose_name="Наличие рыбозащитных устройств")
    max_volume_clean = models.FloatField(null=True, blank=True, verbose_name="Проектный объем забора воды")


class PumpingStation(BaseHydroFacility):
    pumps_count = models.IntegerField(default=0, verbose_name="Количество установленных насосов")
    installed_power = models.FloatField(null=True, blank=True, verbose_name="Суммарная мощность электродвигателей, кВт")
    current_consumption = models.FloatField(null=True, blank=True, verbose_name="Фактический расход энергии")
    head_pressure = models.FloatField(null=True, blank=True, verbose_name="Напор насосной станции, метры водного столба")


class DamsAndDykes(BaseHydroFacility):
    material = models.CharField(max_length=100, null=True, blank=True, verbose_name="Материал сооружения (Земляная, бетонная, каменно-набросная)")
    crest_length = models.FloatField(null=True, blank=True, verbose_name="Длина по гребню, м")
    max_height = models.FloatField(null=True, blank=True, verbose_name="Максимальная высота сооружения, м")
    reservoir_volume = models.FloatField(null=True, blank=True, verbose_name="Объем удерживаемого водохранилища, млн м3")
    is_declared_dangerous = models.BooleanField(default=False, verbose_name="Относится ли к декларируемым аварийным объектам")
