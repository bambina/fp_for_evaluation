from django.core.paginator import Paginator
from django.shortcuts import render
from faqs.models import *


def faq_list(request):
    faqs = FAQEntry.objects.all()
    paginator = Paginator(faqs, 4)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "faqs/list.html", {"faqs": page_obj})
