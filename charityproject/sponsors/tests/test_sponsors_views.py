import pytest
from django.urls import reverse

from model_bakery import baker
from sponsors.models import *
from sponsors.constants import *
from django.core.paginator import Paginator


@pytest.mark.django_db
class TestSponsorViews:
    @pytest.fixture
    def list_url(self):
        # URL for the child list page
        return reverse("sponsors:child_list")

    @pytest.fixture
    def detail_url(self, child_data):
        # URL for the child detail page
        return reverse("sponsors:child_detail", kwargs={"pk": child_data.pk})

    @pytest.fixture
    def child_data(self):
        # Create a child with related gender and country
        gender = baker.make(Gender, name="Male")
        country = baker.make(Country, name="Uganda")
        return baker.make(
            Child,
            name="Carlos",
            age=10,
            gender=gender,
            country=country,
            profile_description="He enjoys painting and dreams of becoming an artist.",
        )

    @pytest.fixture
    def children_data(self):
        gender1 = baker.make(Gender, name="Male")
        gender2 = baker.make(Gender, name="Female")
        country1 = baker.make(Country, name="Uganda")
        country2 = baker.make(Country, name="Kenya")

        baker.make(Child, name="Carlos", age=10, country=country1, gender=gender1)
        baker.make(Child, name="John", age=7, country=country2, gender=gender1)
        baker.make(Child, name="Maria", age=5, country=country2, gender=gender2)
        return {"kenya": country2}

    @pytest.fixture
    def paginated_children(self):
        """Create 20 children for testing pagination (6 per page)"""
        country = baker.make(Country, name="Kenya")
        gender1 = baker.make(Gender, name="Male")
        gender2 = baker.make(Gender, name="Female")
        baker.make(Child, _quantity=10, country=country, gender=gender1)
        baker.make(Child, _quantity=10, country=country, gender=gender2)
        return Child.objects.all().order_by("name")

    def test_child_list_page_contains_expected_content(
        self, client, list_url, child_data
    ):
        """
        Ensure the Child list page returns 200, lists child information,
        and includes the header and footer.
        """
        response = client.get(list_url)
        assert response.status_code == 200

        decoded_content = response.content.decode("utf-8")
        assert child_data.name in decoded_content
        assert str(child_data.country) in decoded_content
        assert "<header" in decoded_content
        assert "<footer" in decoded_content

    def test_child_detail_page_contains_expected_content(
        self, client, detail_url, child_data
    ):
        """
        Ensure the Child detail page returns 200, shows child details,
        and includes the header and footer.
        """
        response = client.get(detail_url)
        assert response.status_code == 200

        decoded_content = response.content.decode("utf-8")
        assert child_data.name in decoded_content
        assert str(child_data.age) in decoded_content
        assert str(child_data.country) in decoded_content
        assert "<header" in decoded_content
        assert "<footer" in decoded_content

    def test_child_list_when_no_children_exists(self, client, list_url):
        """
        Ensure the page returns 200, displays the title, and shows a message when no children are available.
        """
        response = client.get(list_url)
        assert response.status_code == 200
        decoded_content = response.content.decode("utf-8")
        assert "Sponsor a Child" in decoded_content
        assert "No children found matching your criteria." in decoded_content

    def test_child_list_filters_by_multiple_conditions(
        self, client, list_url, children_data
    ):
        """
        Test if the page correctly filters children by multiple conditions:
        - Country (Kenya)
        - Gender (Girls)
        - Max Age (5)
        """
        form_data = {
            "country": children_data["kenya"].id,
            "gender": "Girls",
            "max_age": 5,
        }
        response = client.get(list_url, form_data)
        decoded_content = response.content.decode("utf-8")
        # Should show only one child
        assert "Maria" in decoded_content
        assert "Carlos" not in decoded_content
        assert "John" not in decoded_content

    def test_child_list_shows_no_results_for_country_without_children(
        self, client, list_url, children_data
    ):
        """Test if the page shows 'no results' message when searching for a country that has no children"""
        empty_country = baker.make(Country)

        form_data = {"country": empty_country.id}
        response = client.get(list_url, form_data)
        content = response.content.decode("utf-8")
        assert "No children found matching your criteria." in content

    def test_child_list_shows_error_for_invalid_country_id(
        self, client, list_url, children_data
    ):
        """Test if the form shows validation error when selecting a non-existent country ID"""
        NON_EXISTENT_COUNTRY_ID = 999
        form_data = {"country": NON_EXISTENT_COUNTRY_ID}

        response = client.get(list_url, form_data)
        content = response.content.decode("utf-8")
        assert (
            "Select a valid choice. That choice is not one of the available choices."
            in content
        )

    def test_child_list_pagination_second_page(
        self, client, list_url, paginated_children
    ):
        """Test if pagination shows correct children on the second page"""
        # Get second page
        response = client.get(list_url, {"page": 2})
        content = response.content.decode("utf-8")

        # Assertions
        assert response.status_code == 200
        assert '<a class="page-link" href="?page=1">1</a>' in content
        assert '<a class="page-link" href="#">2</a>' in content

        # Content assertions
        paginator = Paginator(paginated_children, CHILDREN_ITEMS_PER_PAGE)
        second_page_children = paginator.get_page(2)
        for child in second_page_children:
            assert child.name in content

    def test_child_list_pagination_with_query_params(
        self, client, list_url, paginated_children
    ):
        """Test if pagination works correctly with additional query parameters"""
        response = client.get(list_url, {"page": 2, "gender": "Girls"})
        content = response.content.decode("utf-8")

        # Assertions
        assert response.status_code == 200
        assert 'href="?page=1&amp;gender=Girls">Previous</a>' in content
        assert '<a class="page-link" href="#">2</a>' in content

        # Content assertions
        female_children = paginated_children.filter(gender__name="Female").order_by(
            "name"
        )
        paginator = Paginator(female_children, CHILDREN_ITEMS_PER_PAGE)
        second_page_children = paginator.get_page(2)

        for child in second_page_children:
            assert child.name in content
