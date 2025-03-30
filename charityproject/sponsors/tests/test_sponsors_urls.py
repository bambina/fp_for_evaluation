from django.urls import reverse, resolve

from sponsors.views import *


def test_child_list_url():
    """Test for child list page URL configuration"""
    path = reverse("sponsors:child_list")
    assert path == "/sponsors/children/"
    assert resolve(path).func == child_list


def test_child_detail_url():
    """Test for child detail page URL configuration"""
    path = reverse("sponsors:child_detail", kwargs={"pk": 1})
    assert path == "/sponsors/children/1/"
    assert resolve(path).func == child_detail


def test_sponsor_me_button_click_url():
    """Test for sponsor me button click URL configuration"""
    path = reverse("sponsors:sponsor_me_button_click", kwargs={"child_id": 1})
    assert path == "/sponsors/sponsor-me/1/"
    assert resolve(path).func == sponsor_me_button_click
