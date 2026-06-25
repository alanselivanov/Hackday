from django.contrib import admin

from osm_import.models import OSMImportRecord


@admin.register(OSMImportRecord)
class OSMImportRecordAdmin(admin.ModelAdmin):
    list_display = ("osm_type", "osm_id", "facility_type", "object_id", "last_seen_at")
    list_filter = ("facility_type", "osm_type")
    search_fields = ("osm_id", "facility_type")
