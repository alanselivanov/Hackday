"""Маршрут временной демо-страницы. Удаляется вместе с папкой ingestion/demo/."""

from django.urls import path

from . import views

urlpatterns = [
    path("demo/import/", views.import_demo, name="import-demo"),
    path("demo/import/run/", views.import_demo_run, name="import-demo-run"),
    path("demo/import/sample.csv", views.sample_csv, name="import-demo-sample"),
]
