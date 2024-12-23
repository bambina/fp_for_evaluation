from django.core.management.base import BaseCommand
from django.conf import settings
from sponsors.models import *
import csv
from django.core.exceptions import ValidationError
from pathlib import Path
from core.validators import *
from core.utils import *


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

    def handle(self, *args, **kwargs):
        # Get the file path from the command line arguments
        file_paths = {
            "country": Path(settings.DATA_DIR) / kwargs["country"],
        }
        for file_path in file_paths.values():
            if not file_path.exists():
                raise FileNotFoundError(f"File {file_path} not found")

        total_records = 0

        try:
            # Delete exisiting data
            Country.objects.all().delete()

            # Populate the database
            country_records = self.read_country_data(file_paths["country"])
            Country.objects.bulk_create(country_records)
            write_success(
                self.stdout,
                self.style,
                f"{len(country_records)} countries created from {kwargs['country']}",
            )
            total_records += len(country_records)

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
