from django.urls import path
from core import views

urlpatterns = [
    path("", views.top, name="top"),
]
