from django.core.management.base import BaseCommand
from django.conf import settings
from faqs.models import *
import csv
from django.core.exceptions import ValidationError
from pathlib import Path
from core.validators import max_length_255_validator


class Command(BaseCommand):
    # python manage.py populate_data --help
    help = "Populate the database with sample data.\n\n"

    def handle(self, *args, **kwargs):
        total_records = 0

        try:
            # Delete exisiting data
            FAQEntry.objects.all().delete()

            # Populate the database
            faq_records = self.read_faq_data()
            FAQEntry.objects.bulk_create(faq_records)
            self.stdout.write(
                self.style.SUCCESS(f"{len(faq_records)} faqs created from data/faq.csv")
            )
            total_records += len(faq_records)

            print(f"Total records created: {total_records}")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"An error occurred while populating the database: {e}"
                )
            )

    def read_faq_data(self):
        faqs = []
        file_path = Path(settings.DATA_DIR) / "faq.csv"

        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")

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
                    print(f"Validation error in row {csv_reader.line_num}: {e}")
                    continue
        return faqs
