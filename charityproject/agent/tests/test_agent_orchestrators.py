import pytest
from agent.orchestrators import *


class TestOpenAIInteractionOrchestrator:
    def test_build_child_filters(self):
        """
        Test if build_child_filters correctly transforms input arguments into filter conditions.
        """
        arguments = {
            "gender": "female",
            "country": "Bolivia",
            "min_age": 5,
            "max_age": 10,
            "birth_month": 3,
            "birth_day": 15,
        }
        expected_filters = {
            "gender__name__iexact": "female",
            "country__name__iexact": "Bolivia",
            "age__gte": 5,
            "age__lte": 10,
            "date_of_birth__month": 3,
            "date_of_birth__day": 15,
        }

        filters = OpenAIInteractionOrchestrator.build_child_filters(arguments)

        assert filters == expected_filters

    def test_build_child_filters_empty_input(self):
        """
        Test if build_child_filters returns an empty dictionary when given an empty input.
        """
        arguments = {}
        expected_filters = {}

        filters = OpenAIInteractionOrchestrator.build_child_filters(arguments)

        assert filters == expected_filters

    def test_build_child_filters_partial_input(self):
        """
        Test if build_child_filters correctly handles partial input.
        """
        arguments = {"gender": "male", "birth_day": 25}
        expected_filters = {"gender__name__iexact": "male", "date_of_birth__day": 25}

        filters = OpenAIInteractionOrchestrator.build_child_filters(arguments)

        assert filters == expected_filters
