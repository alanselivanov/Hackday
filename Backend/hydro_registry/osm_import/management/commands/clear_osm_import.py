from django.core.management.base import BaseCommand

from infrastructure.models import Canal, DamsAndDykes, PumpingStation, Sluice, WaterIntake
from osm_import.models import OSMImportRecord


class Command(BaseCommand):
    help = "Удалить объекты импорта OSM и связанные записи перед повторным импортом"

    def handle(self, *args, **options):
        osm_count = OSMImportRecord.objects.count()

        canal_count = Canal.objects.count()
        sluice_count = Sluice.objects.count()
        intake_count = WaterIntake.objects.count()
        pumping_count = PumpingStation.objects.count()
        dam_count = DamsAndDykes.objects.count()

        OSMImportRecord.objects.all().delete()
        Canal.objects.all().delete()
        Sluice.objects.all().delete()
        WaterIntake.objects.all().delete()
        PumpingStation.objects.all().delete()
        DamsAndDykes.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Данные импорта OSM удалены"))
        self.stdout.write(f"  OSMImportRecord: {osm_count}")
        self.stdout.write(f"  Canal: {canal_count}")
        self.stdout.write(f"  Sluice: {sluice_count}")
        self.stdout.write(f"  WaterIntake: {intake_count}")
        self.stdout.write(f"  PumpingStation: {pumping_count}")
        self.stdout.write(f"  DamsAndDykes: {dam_count}")
        self.stdout.write("")
        self.stdout.write("Запустите: python manage.py import_osm_facilities")
