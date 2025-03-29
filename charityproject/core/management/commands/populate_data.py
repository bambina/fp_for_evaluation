from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Populate initial data for the project."

    def handle(self, *args, **options):
        commands = [
            "populate_sponsor_data",
            "populate_faq_data",
            "sync_child_vectors",
            "sync_faq_vectors",
        ]

        for cmd in commands:
            self.stdout.write(self.style.NOTICE(f"Running command: {cmd}"))
            call_command(cmd)
            self.stdout.write(self.style.SUCCESS(f"Finished command: {cmd}"))
