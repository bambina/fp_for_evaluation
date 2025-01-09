from django.shortcuts import render
from django.core.paginator import Paginator

from sponsors.models import *


def child_list(request):
    children = Child.objects.all()
    paginator = Paginator(children, 4)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "sponsors/child_list.html", {"children": page_obj})
