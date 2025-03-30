from django.urls import resolve, reverse
from faqs.views import faq_list


def test_faq_list_url():
    path = reverse("faq_list")
    assert resolve(path).func == faq_list
