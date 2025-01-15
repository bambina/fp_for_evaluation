import kagglehub
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    # python manage.py download_use_model --help
    help = "Downloads the Google Universal Sentence Encoder model.\n\n"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force the download of the model, even if it's cached.",
        )

    def handle(self, *args, **kwargs):
        force_download = kwargs.get("force", False)
        MODEL_HANDLE = "google/universal-sentence-encoder/tensorFlow2/multilingual"
        self.stdout.write(
            self.style.SUCCESS(
                f"Downloading the Google Universal Sentence Encoder model {MODEL_HANDLE}..."
            )
        )
        try:
            path = kagglehub.model_download(MODEL_HANDLE, force_download=force_download)
        except RuntimeError as e:
            self.stdout.write(self.style.ERROR(f"Error downloading model: {e}"))
            return
        print("Path to model files:", path)
        self.stdout.write(self.style.SUCCESS("Model downloaded successfully!"))
