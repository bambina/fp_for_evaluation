from django.urls import path
from sponsors import views

app_name = "sponsors"

urlpatterns = [
    path("children/", views.child_list, name="child_list"),
    path("children/<int:pk>/", views.child_detail, name="child_detail"),
    path(
        "sponsor-me/<int:child_id>/",
        views.sponsor_me_button_click,
        name="sponsor_me_button_click",
    ),
]
