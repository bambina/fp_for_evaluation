from django.db import models


class FAQEntry(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "FAQ Entry"
        verbose_name_plural = "FAQ Entries"
        indexes = [
            models.Index(fields=["question", "answer"]),
        ]

    def __str__(self):
        return self.question
