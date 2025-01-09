from django.core.management.base import BaseCommand
from django.conf import settings
from sponsors.models import *
import csv
from django.core.exceptions import ValidationError
from pathlib import Path
from core.validators import *
from core.utils import *
from sponsors.utils import *


class Command(BaseCommand):
    # python manage.py populate_sponsor_data --help
    help = "Populate the database with sample data.\n\n"

    def add_arguments(self, parser):
        # Add an optional argument to specify the CSV file to load data from
        parser.add_argument(
            "--country",
            type=str,
            default="countries.csv",
            help="The CSV file to load data from (default: countries.csv).",
        )
        parser.add_argument(
            "--gender",
            type=str,
            default="genders.csv",
            help="The CSV file to load data from (default: genders.csv).",
        )
        parser.add_argument(
            "--child",
            type=str,
            default="children.csv",
            help="The CSV file to load data from (default: children.csv).",
        )

    def handle(self, *args, **kwargs):
        # Get the file path from the command line arguments
        file_paths = {
            "country": Path(settings.DATA_DIR) / kwargs["country"],
            "gender": Path(settings.DATA_DIR) / kwargs["gender"],
            "child": Path(settings.DATA_DIR) / kwargs["child"],
        }
        for file_path in file_paths.values():
            if not file_path.exists():
                raise FileNotFoundError(f"File {file_path} not found")

        total_records = 0

        try:
            # Delete exisiting data
            Child.objects.all().delete()
            Country.objects.all().delete()
            Gender.objects.all().delete()

            # Populate the database
            country_records = self.read_country_data(file_paths["country"])
            Country.objects.bulk_create(country_records)
            write_success(
                self.stdout,
                self.style,
                f"{len(country_records)} items created from {kwargs['country']}",
            )
            total_records += len(country_records)

            gender_records = self.read_gender_data(file_paths["gender"])
            Gender.objects.bulk_create(gender_records)
            write_success(
                self.stdout,
                self.style,
                f"{len(gender_records)} items created from {kwargs['gender']}",
            )
            total_records += len(gender_records)

            childlen_records = self.read_child_data(file_paths["child"])
            Child.objects.bulk_create(childlen_records)
            write_success(
                self.stdout,
                self.style,
                f"{len(childlen_records)} items created from {kwargs['child']}",
            )
            total_records += len(childlen_records)

            write_success(
                self.stdout, self.style, f"Total records created: {total_records}"
            )
        except Exception as e:
            write_error(
                self.stdout,
                self.style,
                f"An error occurred while populating the database: {e}",
            )

    def read_country_data(self, file_path):
        countries = []
        with open(file_path, mode="r", encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            csv_reader.__next__()
            for row in csv_reader:
                try:
                    # Assign the row data to variables
                    numeric_code = row[0].strip()
                    code = row[1].strip()
                    name = row[2].strip()
                    if not numeric_code or not code or not name:
                        raise ValidationError(
                            "Numeric code, code and name cannot be empty"
                        )
                    # Validate the question length
                    numeric_code_validator(numeric_code)
                    alpha_2_code_validator(code)
                    max_length_255_validator(name)
                    countries.append(
                        Country(numeric_code=numeric_code, code=code, name=name)
                    )
                except ValidationError as e:
                    write_error(
                        self.stdout,
                        self.style,
                        f"Validation error in row {csv_reader.line_num}: {e}",
                    )
                    continue
        return countries

    def read_gender_data(self, file_path):
        genders = []
        with open(file_path, mode="r", encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            csv_reader.__next__()
            for row in csv_reader:
                try:
                    # Assign the row data to variables
                    name = row[0].strip()
                    if not name:
                        raise ValidationError("Name cannot be empty")
                    # Validate the question length
                    max_length_50_validator(name)
                    genders.append(Gender(name=name))
                except ValidationError as e:
                    write_error(
                        self.stdout,
                        self.style,
                        f"Validation error in row {csv_reader.line_num}: {e}",
                    )
                    continue
        return genders

    def read_child_data(self, file_path):
        children = []
        with open(file_path, mode="r", encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            csv_reader.__next__()
            for row in csv_reader:
                try:
                    # Extract and clean the row data
                    name = row[0].strip()
                    gender = Gender.objects.get(name=row[1].strip())
                    country = Country.objects.get(name=row[2].strip())
                    profile_description = row[3].strip()
                    birth_date_str = row[4].strip()
                    # Validate individual fields
                    max_length_255_validator(name)
                    validate_birth_date(birth_date_str)
                    # Compute age from birth date
                    age = calculate_age(birth_date_str)
                    # Create and append the child object
                    children.append(
                        Child(
                            name=name,
                            age=age,
                            gender=gender,
                            country=country,
                            profile_description=profile_description,
                            date_of_birth=birth_date_str,
                        )
                    )
                except Exception as e:
                    write_error(
                        self.stdout,
                        self.style,
                        f"Exception in row {csv_reader.line_num}: {e}",
                    )
                    continue
        return children
