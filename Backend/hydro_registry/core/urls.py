from django.urls import path

from core.views import FacilityListAPIView

urlpatterns = [
    path("facilities/", FacilityListAPIView.as_view(), name="facility-list"),
]
