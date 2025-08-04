
# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Genre(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Mood(models.Model):
    name = models.CharField(max_length=50)
    emoji = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.emoji} {self.name}"

class Drama(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dramas')
    title = models.CharField(max_length=200)
    description = models.TextField()
    poster = models.ImageField(upload_to="posters/", blank=True, null=True)
    release_year = models.IntegerField()
    total_episodes = models.IntegerField()
    genres = models.ManyToManyField('Genre', blank=True)
    moods = models.ManyToManyField('Mood', blank=True)
    spotify_link = models.URLField(blank=True)

    class Meta:
        unique_together = ['user', 'title']

    def __str__(self):
        return self.title
