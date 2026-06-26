from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics"

    def ready(self):
        # Навешиваем классификатор модуля 6 методом, не раздувая models.py.
        # Импорт здесь (а не на верхнем уровне), т.к. модели загружаются после ready-старта.
        from analytics.models import FacilityAnalytics
        from analytics.services import recalculate_status

        FacilityAnalytics.recalculate = recalculate_status
