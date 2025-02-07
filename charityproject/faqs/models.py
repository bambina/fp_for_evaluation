from django.db import models

from core.constants import *


class FAQEntry(models.Model):
    question = models.CharField(max_length=MAX_QUESTION_LEN)
    answer = models.TextField(max_length=MAX_ANSWER_LEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "FAQ Entry"
        verbose_name_plural = "FAQ Entries"
        indexes = [
            models.Index(fields=["question", "answer"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return self.question
