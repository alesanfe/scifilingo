"""Database models for the translation app."""

from django.contrib.auth.models import User
from django.db import models


class Translation(models.Model):
    """Stores a single translation made by a user.

    Each record captures the original text, the translated text, the target
    fictional language, and the timestamp of the translation.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_text = models.TextField()
    translated_text = models.TextField()
    target_language = models.CharField(max_length=50)
    translation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model metadata options."""

        ordering = ["-translation_date", "-id"]

    def __str__(self):
        """Return a human-readable representation of the translation."""
        return f"Translation #{self.id} by {self.user.username}"
