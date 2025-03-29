from django.db import models

from agent.constants import MessageSender


class ChatMessage(models.Model):
    """
    Model for storing chat messages in a conversation."
    """

    session_id = models.CharField(max_length=50)
    sender_type = models.CharField(max_length=10, choices=MessageSender.CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        """
        Returns a string representation of the message with truncated content.
        """
        return f"{self.session_id}({self.sender_type}) - {self.content[:20]}"
