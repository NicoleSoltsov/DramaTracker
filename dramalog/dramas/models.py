
# Create your models here.
from django.db import models

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
    title = models.CharField(max_length=200)
    description = models.TextField()
    poster = models.ImageField(upload_to='posters/')
    release_year = models.IntegerField()
    total_episodes = models.IntegerField()
    genres = models.ManyToManyField(Genre)
    moods = models.ManyToManyField(Mood)
    spotify_link = models.URLField(blank=True)

    def __str__(self):
        return self.title
