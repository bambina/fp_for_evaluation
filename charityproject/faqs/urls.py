from django.urls import path
from faqs import views

app_name = "faqs"

urlpatterns = [
    path("", views.faq_list, name="faq_list"),
    path("<int:pk>/", views.faq_detail, name="faq_detail"),
]
