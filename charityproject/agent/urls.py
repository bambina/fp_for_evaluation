from django.urls import path
from agent import views

app_name = "agent"

urlpatterns = [
    path("start/", views.start_chat, name="start-chat"),
]
