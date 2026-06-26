from django.core.management.base import BaseCommand

from analytics.calculation_inputs import ensure_calculation_inputs
from analytics.services import recalculate_status
from core.models import BaseHydroFacility
from inspection_service import run_for_facility


def calculate_importance(facility: BaseHydroFacility) -> str:
    if facility.facility_type in ("dam_dyke", "pumping"):
        return "high"
    if facility.facility_type in ("sluice", "intake"):
        return "medium"
    if facility.is_emergency_prone:
        return "high"
    return "low"


class Command(BaseCommand):
    help = "Пересчитать интервалы осмотров и статусы ремонта для всех гидросооружений."

    def handle(self, *args, **options):
        total = 0
        errors = 0

        for facility in BaseHydroFacility.objects.all().order_by("id"):
            total += 1
            try:
                ensure_calculation_inputs(facility)
                result = run_for_facility(facility)
                analytics = facility.analytics
                analytics.calculated_importance = calculate_importance(facility)
                analytics.save(update_fields=["calculated_importance", "updated_at"])
                recalculate_status(analytics)

                marker = "OK"
                if result.error:
                    marker = "FALLBACK"
                self.stdout.write(
                    f"{marker}: {facility.pk} {facility.name} -> "
                    f"{analytics.inspection_interval_days} дней, {analytics.repair_status}"
                )
            except Exception as exc:
                errors += 1
                self.stderr.write(f"ERROR: {facility.pk} {facility.name}: {exc}")

        if errors:
            self.stdout.write(self.style.WARNING(f"Готово: total={total}, errors={errors}"))
            return
        self.stdout.write(self.style.SUCCESS(f"Готово: total={total}, errors=0"))
