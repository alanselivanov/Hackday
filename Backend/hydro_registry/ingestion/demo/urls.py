"""Маршрут временной демо-страницы. Удаляется вместе с папкой ingestion/demo/."""

from django.urls import path

from . import views

urlpatterns = [
    path("demo/import/", views.import_demo, name="import-demo"),
]
