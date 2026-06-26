from django.core.management.base import BaseCommand

from osm_import.services.importer import FacilityImporter


class Command(BaseCommand):
    help = "Импорт гидротехнических сооружений из OpenStreetMap для заданной территории"

    def handle(self, *args, **options):
        importer = FacilityImporter()
        stats = importer.run()

        self.stdout.write(self.style.SUCCESS("Импорт завершён"))
        self.stdout.write(f"  Найдено объектов: {stats.found}")
        self.stdout.write(f"  Создано: {stats.created}")
        self.stdout.write(f"  Уже существовало: {stats.existing}")
        self.stdout.write(f"  Пропущено (классификация): {stats.skipped_classification}")
        self.stdout.write(f"  Ошибок: {stats.errors}")

        if stats.error_details:
            self.stdout.write(self.style.WARNING("Детали ошибок:"))
            for detail in stats.error_details:
                self.stdout.write(f"  - {detail}")
