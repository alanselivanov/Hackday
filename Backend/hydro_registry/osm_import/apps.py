from django.apps import AppConfig


class OsmImportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "osm_import"
    verbose_name = "Импорт OpenStreetMap"
