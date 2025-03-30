from django.urls import resolve, reverse

from faqs.views import *


def test_faq_list_url():
    """Test for FAQ list page URL configuration"""
    path = reverse("faqs:faq_list")
    assert path == "/faqs/"
    assert resolve(path).func == faq_list


def test_faq_detail_url():
    """Test for FAQ detail page URL configuration"""
    path = reverse("faqs:faq_detail", kwargs={"pk": 1})
    assert path == "/faqs/1/"
    assert resolve(path).func == faq_detail
