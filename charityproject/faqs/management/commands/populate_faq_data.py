from django.core.management.base import BaseCommand
from django.conf import settings
from faqs.models import *
import csv
from django.core.exceptions import ValidationError
from pathlib import Path
from core.validators import max_length_255_validator
from core.utils import *


class Command(BaseCommand):
    # python manage.py populate_faq_data --help
    help = "Populate the database with sample data.\n\n"

    def add_arguments(self, parser):
        # Add an optional argument to specify the CSV file to load data from
        parser.add_argument(
            "--faq",
            type=str,
            default="faqs.csv",
            help="The CSV file to load data from (default: faqs.csv).",
        )

    def handle(self, *args, **kwargs):
        # Get the file path from the command line arguments
        file_paths = {
            "faq": Path(settings.DATA_DIR) / kwargs["faq"],
        }
        for file_path in file_paths.values():
            if not file_path.exists():
                raise FileNotFoundError(f"File {file_path} not found")

        total_records = 0

        try:
            # Delete exisiting data
            FAQEntry.objects.all().delete()

            # Populate the database
            faq_records = self.read_faq_data(file_paths["faq"])
            FAQEntry.objects.bulk_create(faq_records)
            write_success(
                self.stdout,
                self.style,
                f"{len(faq_records)} faqs created from {kwargs['faq']}",
            )
            total_records += len(faq_records)

            write_success(
                self.stdout, self.style, f"Total records created: {total_records}"
            )
        except Exception as e:
            write_error(
                self.stdout,
                self.style,
                f"An error occurred while populating the database: {e}",
            )

    def read_faq_data(self, file_path):
        faqs = []
        with open(file_path, mode="r", encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            csv_reader.__next__()
            for row in csv_reader:
                try:
                    # Assign the row data to variables
                    question = row[0].strip()
                    answer = row[1].strip()
                    if not question or not answer:
                        raise ValidationError("Question and answer cannot be empty")
                    # Validate the question length
                    max_length_255_validator(question)
                    faqs.append(FAQEntry(question=question, answer=answer))
                except ValidationError as e:
                    write_error(
                        self.stdout,
                        self.style,
                        f"Validation error in row {csv_reader.line_num}: {e}",
                    )
                    continue
        return faqs
