from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions"
    )
    context_summary = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sesi Chat"
        verbose_name_plural = "Sesi Chat"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Sesi #{self.id} - {self.user.username}"


class ChatMessage(models.Model):
    class SenderType(models.TextChoices):
        USER = "user", "Pengguna"
        AI = "ai", "AI"

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender_type = models.CharField(max_length=10, choices=SenderType.choices)
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pesan Chat"
        verbose_name_plural = "Pesan Chat"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.sender_type}] {self.message_text[:50]}"
