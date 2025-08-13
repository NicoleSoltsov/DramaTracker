# tracker/serializers.py
from rest_framework import serializers
from .models import WatchStatus
from dramas.models import Drama

class WatchStatusSerializer(serializers.ModelSerializer):
    # Use tmdb_id to identify the drama, but only from THIS user
    drama = serializers.SlugRelatedField(
        slug_field='tmdb_id',
        queryset=Drama.objects.none()
    )

    class Meta:
        model = WatchStatus
        fields = '__all__'
        read_only_fields = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # limit queryset at runtime to current user
        req = self.context.get('request')
        if req and req.user and req.user.is_authenticated:
            self.fields['drama'].queryset = Drama.objects.filter(user=req.user)
