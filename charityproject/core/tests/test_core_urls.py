from django.urls import resolve, reverse

from core.views import top


def test_core_top_url():
    """Test for top page URL configuration"""
    path = reverse("core:top")
    assert path == "/"
    assert resolve(path).func == top
