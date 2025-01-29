# templatetags/pagination_utils.py
from django import template
from urllib.parse import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def pagination_query_params(context, **kwargs):
    """
    A template tag for handling pagination query parameters.
    Maintains current GET parameters while setting a new page number.

    Example usage:
    {% pagination_query_params page=2 %}
    """
    query = context["request"].GET.dict()
    query.update(kwargs)
    return "?" + urlencode(query)
