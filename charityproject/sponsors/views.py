from django.shortcuts import render


def child_list(request):
    return render(request, "sponsors/child_list.html")
