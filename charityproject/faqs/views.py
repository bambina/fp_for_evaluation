from django.core.paginator import Paginator
from django.shortcuts import render
from django.shortcuts import get_object_or_404

from faqs.models import *


def faq_list(request):
    """
    Display a paginated list of all FAQ entries.
    """
    faqs = FAQEntry.objects.all()
    paginator = Paginator(faqs, 4)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "faqs/list.html", {"faqs": page_obj})


def faq_detail(request, pk):
    """
    Display the detail view of a single FAQ entry.
    """
    faq = get_object_or_404(FAQEntry, id=pk)
    return render(request, "faqs/detail.html", {"faq": faq})
