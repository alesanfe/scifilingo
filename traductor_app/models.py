from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class Translation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_text = models.TextField()
    translated_text = models.TextField()
    target_language = models.CharField(max_length=50)
    translation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Translation #{self.id} by {self.user.username}'

    class Meta:
        ordering = ['-translation_date']
