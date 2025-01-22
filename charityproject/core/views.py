from django.shortcuts import render


def top(request):
    """View function for the top page."""
    return render(request, "core/top.html")
