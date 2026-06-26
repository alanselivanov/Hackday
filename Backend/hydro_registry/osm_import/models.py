from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class OSMImportRecord(models.Model):
    source = models.CharField(max_length=20, default="osm", verbose_name="Источник")
    osm_type = models.CharField(max_length=10, verbose_name="Тип OSM-элемента")
    osm_id = models.BigIntegerField(verbose_name="OSM ID")
    facility_type = models.CharField(max_length=30, verbose_name="Тип сооружения")
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Тип локальной модели",
    )
    object_id = models.PositiveBigIntegerField(verbose_name="ID локального объекта")
    facility = GenericForeignKey("content_type", "object_id")
    first_imported_at = models.DateTimeField(auto_now_add=True, verbose_name="Первый импорт")
    last_seen_at = models.DateTimeField(auto_now=True, verbose_name="Последнее обнаружение")
    raw_tags = models.JSONField(default=dict, verbose_name="OSM-теги")

    class Meta:
        verbose_name = "Запись импорта OSM"
        verbose_name_plural = "Записи импорта OSM"
        constraints = [
            models.UniqueConstraint(
                fields=["source", "osm_type", "osm_id"],
                name="unique_osm_import_source_type_id",
            ),
        ]
        indexes = [
            models.Index(fields=["source", "osm_type", "osm_id"]),
            models.Index(fields=["facility_type"]),
        ]

    def __str__(self):
        return f"OSM {self.osm_type}/{self.osm_id} -> {self.facility_type}#{self.object_id}"
