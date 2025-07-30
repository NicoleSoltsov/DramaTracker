from rest_framework import serializers
from .models import WatchStatus

class WatchStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchStatus
        fields = '__all__'
