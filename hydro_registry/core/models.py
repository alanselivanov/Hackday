from django.contrib.gis.db import models


class BaseHydroFacility(models.Model):
    FACILITY_TYPES = [
        ('canal', 'Канал'),
        ('post', 'Гидропост'),
        ('sluice', 'Шлюз'),
        ('intake', 'Водозабор'),
        ('pumping', 'Насосная станция'),
        ('dam_dyke', 'Плотина/Дамба')
    ]
    facility_type = models.CharField(max_length=30, choices=FACILITY_TYPES, verbose_name="Тип объекта")
    uid = models.FloatField(null=True, blank=True, verbose_name="№ по реестру")
    name = models.CharField(max_length=255, verbose_name="Наименование")
    water_source = models.CharField(max_length=255, verbose_name="Водоисточник")
    district = models.CharField(max_length=255, verbose_name="Название обслуживаемого района")
    rural_district = models.CharField(max_length=255, null=True, blank=True, verbose_name="Сельский округ")
    cadastral_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="Кадастровый номер")
    state_act = models.CharField(max_length=100, null=True, blank=True, verbose_name="Гос Акт")
    location = models.PointField(srid=4326, null=True, blank=True, verbose_name="Координаты объекта")
    year_built = models.IntegerField(null=True, blank=True, verbose_name="Год ввода в эксплуатацию")
    year_balanced = models.IntegerField(null=True, blank=True, verbose_name="Год принятия на баланс РС")
    wear_percentage = models.FloatField(default=0.0, verbose_name="Процент износа")
    technical_condition = models.CharField(max_length=50, null=True, blank=True, verbose_name="Техническое состояние")
    efficiency_project = models.FloatField(null=True, blank=True, verbose_name="КПД проектный")
    efficiency_fact = models.FloatField(null=True, blank=True, verbose_name="КПД фактический")
    is_emergency_prone = models.BooleanField(default=False, verbose_name="Флаг повышенной аварийности")

    def __str__(self):
        return f"{self.get_facility_type_display()}: {self.name}"
