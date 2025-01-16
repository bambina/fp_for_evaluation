from django.urls import path
from agent import views

urlpatterns = [
    path("start/", views.start_chat, name="start-chat"),
]
