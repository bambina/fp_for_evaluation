from django.shortcuts import render
from django.http import HttpResponse


def faq_list(request):
    return render(request, "faqs/list.html")
