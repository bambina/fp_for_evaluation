from django.urls import path
from core import views

# Define the application namespace
app_name = "core"

urlpatterns = [
    # Top page
    path("", views.top, name="top"),
]
