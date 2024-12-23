from django.urls import path
from sponsors import views

app_name = "sponsors"

urlpatterns = [
    path("children/", views.child_list, name="child_list"),
    # path("children/<int:pk>/", views.child_detail, name="child_detail"),
]
