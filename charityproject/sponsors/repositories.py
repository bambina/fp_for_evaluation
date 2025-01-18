from django.views.generic import ListView
from django.db.models import Q
from django.db.models.query import QuerySet

from sponsors.models import *


class ChildRepository:
    """Repository for Child model."""

    # Mapping of gender filter values
    GENDER_MAP = {
        "Boys": "Male",
        "Girls": "Female",
        "Other": "Other",
    }

    @staticmethod
    def fetch_filtered_by(
        country=None,
        gender=None,
        min_age=None,
        max_age=None,
        birth_month=None,
        birth_day=None,
        keywords=None,
    ) -> QuerySet[Child]:
        """Fetch children that match the given filters."""
        # Base queryset with related fields and necessary attributes
        queryset = (
            Child.objects.filter(deleted_at__isnull=True)
            .select_related("country", "gender")
            .only(
                "name",
                "country",
                "gender",
                "age",
                "date_of_birth",
                "profile_description",
            )
        )

        # Apply filters
        queryset = ChildRepository.apply_age_filter(queryset, min_age, max_age)
        queryset = ChildRepository.apply_country_filter(queryset, country)
        queryset = ChildRepository.apply_gender_filter(queryset, gender)
        queryset = ChildRepository.apply_birth_date_filter(
            queryset, birth_month, birth_day
        )
        queryset = ChildRepository.apply_keywords_filter(queryset, keywords)

        # Return the filtered queryset
        return queryset

    @staticmethod
    def apply_keywords_filter(queryset, keywords):
        """Filter by multiple keywords in name or profile description."""
        if keywords:
            keyword_list = keywords.split()

            for keyword in keyword_list:
                queryset = queryset.filter(
                    Q(name__icontains=keyword)
                    | Q(profile_description__icontains=keyword)
                )
        return queryset

    @staticmethod
    def apply_age_filter(queryset, min_age, max_age):
        """Filter by age range."""
        if min_age:
            queryset = queryset.filter(age__gte=min_age)
        if max_age:
            queryset = queryset.filter(age__lte=max_age)
        return queryset

    @staticmethod
    def apply_country_filter(queryset, country):
        """Filter by country."""
        if country:
            queryset = queryset.filter(country=country)
        return queryset

    @staticmethod
    def apply_gender_filter(queryset, gender):
        """Filter by gender."""
        if gender and gender != "All":
            db_gender = ChildRepository.GENDER_MAP.get(gender)
            if db_gender:
                queryset = queryset.filter(gender__name=db_gender)
        return queryset

    @staticmethod
    def apply_birth_date_filter(queryset, birth_month, birth_day):
        """Filter by birth month and day."""
        if birth_month:
            queryset = queryset.filter(date_of_birth__month=int(birth_month))
        if birth_day:
            queryset = queryset.filter(date_of_birth__day=int(birth_day))
        return queryset
