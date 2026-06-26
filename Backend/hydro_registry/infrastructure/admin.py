from django.contrib import admin

from infrastructure.models import (
    Canal,
    DamsAndDykes,
    PumpingStation,
    Sluice,
    WaterIntake,
)


@admin.register(Canal)
class CanalAdmin(admin.ModelAdmin):
    list_display = ("name", "facility_type", "district", "total_length", "capacity")
    search_fields = ("name", "district", "water_source")


@admin.register(Sluice)
class SluiceAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "gates_count", "max_discharge")
    search_fields = ("name", "district")


@admin.register(WaterIntake)
class WaterIntakeAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "intake_type", "max_volume_clean")
    search_fields = ("name", "district")


@admin.register(PumpingStation)
class PumpingStationAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "pumps_count", "installed_power")
    search_fields = ("name", "district")


@admin.register(DamsAndDykes)
class DamsAndDykesAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "material", "crest_length", "max_height")
    search_fields = ("name", "district")

