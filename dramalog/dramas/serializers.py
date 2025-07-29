from rest_framework import serializers
from .models import *

class DramaSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    moods = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Drama
        fields = '__all__'