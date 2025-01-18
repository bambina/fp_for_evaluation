from django.shortcuts import render
from django.core.paginator import Paginator
from sponsors.repositories import *
from sponsors.models import *
from sponsors.forms import ChildSearchForm
from django.shortcuts import get_object_or_404

from core.utils import track_user_with_session
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse


def child_list(request):
    """List view for children with search and pagination."""
    # Track user with session key
    track_user_with_session(request, event="Viewed Child List")

    # Save search query to session if exists, otherwise clear it
    if request.GET:
        request.session["child_list_query"] = request.GET.urlencode()
    else:
        request.session.pop("child_list_query", None)

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


def child_detail(request, pk):
    """Detail view for a specific child."""
    # Track user with session key
    track_user_with_session(request, event=f"Viewed Child Detail. Child ID: {pk}")

    # Get the child object or return 404
    child = get_object_or_404(Child, pk=pk)

    # Get saved search query from session
    query_string = request.session.get("child_list_query", "")

    # Pass the query string to the template
    return render(
        request,
        "sponsors/child_detail.html",
        {"child": child, "query_string": query_string},
    )


@csrf_exempt
def sponsor_me_button_click(request, child_id):
    """Handle Sponsor Me button click event."""
    if request.method == "POST":
        track_user_with_session(
            request, f"Clicked Sponsor Me Button for Child ID: {child_id}"
        )
        messages.success(
            request,
            "Thank you for your kindness! Your support helps create brighter futures.",
        )

        # Redirect to the child detail page
        return redirect("sponsors:child_detail", pk=child_id)

    return JsonResponse({"error": "Invalid request method"}, status=400)


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
        keywords = search_form.cleaned_data.get("keywords")

        children = ChildRepository.fetch_filtered_by(
            country, gender, min_age, max_age, birth_month, birth_day, keywords
        )

    return children


def paginate_children(children, request):
    """Paginate the child data."""
    paginator = Paginator(children, 6)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)
