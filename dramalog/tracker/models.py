from django.db import models
from django.contrib.auth import get_user_model
from dramas.models import Drama  # assumes Drama is in dramas app

User = get_user_model()

class WatchStatus(models.Model):
    STATUS_CHOICES = [
        ("plan", "Plan to Watch"),
        ("watching", "Watching"),
        ("on_hold", "On Hold"),
        ("dropped", "Dropped"),
        ("finished", "Finished"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    drama = models.ForeignKey(Drama, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    current_episode = models.PositiveIntegerField(default=0)
    rewatch_count = models.PositiveIntegerField(default=0)
    personal_rating = models.IntegerField(null=True, blank=True)  # 1–10
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'drama']  # Each user can track a drama once

    def __str__(self):
        return f"{self.user.username} - {self.drama.title} ({self.status})"
