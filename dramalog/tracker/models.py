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
    # NEW: season-aware progress
    current_season = models.PositiveIntegerField(default=1)
    current_episode = models.PositiveIntegerField(default=0)
    rewatch_count = models.PositiveIntegerField(default=0)
    personal_rating = models.IntegerField(null=True, blank=True)  # 1–10
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'drama']  # Each user can track a drama once

    def __str__(self):
        return f"{self.user.username} - {self.drama.title} ({self.status})"

# NEW: per-episode journal entries
class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="journal_entries")
    drama = models.ForeignKey(Drama, on_delete=models.CASCADE, related_name="journal_entries")
    # store season/episode
    season = models.PositiveIntegerField(default=1)
    episode = models.PositiveIntegerField(default=1)

    # entry content
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True)

    # optional linkage to the user's watch status for convenience/ownership
    watch_status = models.ForeignKey(
        WatchStatus, on_delete=models.CASCADE, related_name="journal_entries", null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # OPTION A (diary-style, allow multiple entries per episode): no constraint
    # OPTION B (strict: one entry per (user, drama, season, episode)):
    # class Meta:
    #     unique_together = [("user", "drama", "season", "episode")]

    class Meta:
        indexes = [
            models.Index(fields=["user", "drama", "season", "episode"]),
            models.Index(fields=["-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} • {self.drama.title} S{self.season}E{self.episode} • {self.created_at:%Y-%m-%d}"
