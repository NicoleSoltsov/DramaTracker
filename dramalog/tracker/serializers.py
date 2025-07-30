from rest_framework import serializers
from .models import WatchStatus, Drama

class WatchStatusSerializer(serializers.ModelSerializer):
    drama = serializers.SlugRelatedField(
        slug_field='title',
        queryset=Drama.objects.all()
    )

    class Meta:
        model = WatchStatus
        fields = '__all__'
        read_only_fields = ['user']
