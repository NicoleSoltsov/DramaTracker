from rest_framework import serializers
from .models import Review
from dramas.models import Drama

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    drama = serializers.CharField()  # Accept drama as a title (string)

    class Meta:
        model = Review
        fields = ['id', 'user', 'drama', 'content', 'created_at', 'updated_at']

    def validate_drama(self, value):
        try:
            return Drama.objects.get(title__iexact=value, user=self.context['request'].user)
        except Drama.DoesNotExist:
            raise serializers.ValidationError("Drama not found in your list.")

    def create(self, validated_data):
        drama = validated_data.pop('drama')
        return Review.objects.create(drama=drama, **validated_data)
 