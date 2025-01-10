from django.shortcuts import render
from django.core.paginator import Paginator
from sponsors.repositories import *
from sponsors.models import *
from sponsors.forms import ChildSearchForm


def child_list(request):
    # Init the search form
    search_form = ChildSearchForm(request.GET or None)

    # Get filtered child data
    children = get_filtered_children(search_form)

    # Paginate the child data
    page_obj = paginate_children(children, request)

    # Create the context for rendering
    context = {
        "children": page_obj,
        "search_form": search_form,
    }

    return render(request, "sponsors/child_list.html", context)


def get_filtered_children(search_form):
    """Filter child data based on search form input."""
    # Retrieve all children with related country data
    children = Child.objects.select_related("country")

    # Apply filters if the search form is valid
    if search_form.is_valid():
        country = search_form.cleaned_data.get("country")
        gender = search_form.cleaned_data.get("gender")
        min_age = search_form.cleaned_data.get("min_age")
        max_age = search_form.cleaned_data.get("max_age")
        birth_month = search_form.cleaned_data.get("birth_month")
        birth_day = search_form.cleaned_data.get("birth_day")

        children = ChildRepository.fetch_filtered_by(
            country, gender, min_age, max_age, birth_month, birth_day
        )

    return children


def paginate_children(children, request):
    """Paginate the child data."""
    paginator = Paginator(children, 6)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)
