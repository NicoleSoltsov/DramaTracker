from rest_framework import serializers
from .models import *

class DramaSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Genre.objects.all()
    )
    moods = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Mood.objects.all()
    )
    pinterest_search_url = serializers.SerializerMethodField()
    def get_pinterest_search_url(self, obj):
        title = obj.title or ""
        query = f"{title} aesthetic board".replace(" ", "%20")
        return f"https://www.pinterest.com/search/boards/?q={query}"

    class Meta:
        model = Drama
        exclude = ['user']


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'

class MoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mood
        fields = '__all__'