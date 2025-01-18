from django import forms
from sponsors.models import *
from calendar import month_name


class ChildSearchForm(forms.Form):
    """Search form for locating children in the Sponsor a Child program by criteria such as age, gender, or country."""

    # Common widget attributes
    form_control_class = {"class": "form-control"}

    country = forms.ModelChoiceField(
        required=False,
        queryset=Country.objects.all(),
        label="Country",
        empty_label="All Countries",
        widget=forms.Select(attrs=form_control_class),
    )

    gender = forms.ChoiceField(
        required=False,
        choices=[
            ("All", "All"),
            ("Boys", "Boys"),
            ("Girls", "Girls"),
            ("Other", "Other"),
        ],
        label="Gender",
        initial="All",
        widget=forms.Select(attrs=form_control_class),
    )

    min_age = forms.IntegerField(
        required=False,
        label="Min Age",
        min_value=0,
        widget=forms.NumberInput(
            attrs={"placeholder": "Min age", **form_control_class}
        ),
    )

    max_age = forms.IntegerField(
        required=False,
        label="Max Age",
        min_value=0,
        widget=forms.NumberInput(
            attrs={"placeholder": "Max age", **form_control_class}
        ),
    )

    birth_month = forms.ChoiceField(
        required=False,
        # Generate dropdown options for months
        choices=[("", "All Months")] + [(str(i), month_name[i]) for i in range(1, 13)],
        label="Birth Month",
        widget=forms.Select(attrs=form_control_class),
    )

    birth_day = forms.ChoiceField(
        required=False,
        # Generate dropdown options for days
        choices=[("", "All Days")] + [(str(i), str(i)) for i in range(1, 32)],
        label="Birth Day",
        widget=forms.Select(attrs=form_control_class),
    )

    keywords = forms.CharField(
        required=False,
        label="Keywords",
        widget=forms.TextInput(
            attrs={"placeholder": "Search by name or profile", **form_control_class}
        ),
    )

    def clean(self):
        """Validate form data before processing."""
        cleaned_data = super().clean()
        min_age = cleaned_data.get("min_age")
        max_age = cleaned_data.get("max_age")

        # Ensure minimum age is not greater than maximum age
        if min_age is not None and max_age is not None:
            if min_age > max_age:
                raise forms.ValidationError(
                    "Minimum age cannot be greater than maximum age."
                )

        return cleaned_data
