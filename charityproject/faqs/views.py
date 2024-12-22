from django.shortcuts import render
from django.http import HttpResponse


def faq_list(request):
    return HttpResponse("This is the FAQ list page.")
