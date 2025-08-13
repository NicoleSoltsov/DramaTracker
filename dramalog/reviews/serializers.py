from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import Review
from dramas.models import Drama
from django.db import IntegrityError

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    # Accept tmdb_id or title
    drama = serializers.CharField(write_only=True)
    rating = serializers.IntegerField(min_value=1, max_value=10)

    class Meta:
        model = Review
        fields = ['id', 'user', 'drama', 'content', 'rating', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_drama(self, value):
        user = self.context['request'].user
        if isinstance(value, int) or (isinstance(value, str) and value.strip().isdigit()):
            tmdb_id = int(value)
            try:
                return Drama.objects.get(user=user, tmdb_id=tmdb_id)
            except Drama.DoesNotExist:
                raise serializers.ValidationError("No drama with that TMDB id in your list.")
        title = str(value).strip()
        qs = Drama.objects.filter(user=user, title__iexact=title)
        count = qs.count()
        if count == 0:
            raise serializers.ValidationError("Drama not found in your list.")
        if count > 1:
            raise serializers.ValidationError("Multiple dramas share that title. Please send the TMDB id.")
        return qs.first()

    def create(self, validated_data):
        drama = validated_data.pop('drama')
        try:
            return Review.objects.create(drama=drama, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError("You’ve already reviewed this drama.")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['drama'] = instance.drama.title
        data['drama_tmdb_id'] = instance.drama.tmdb_id  # new field for frontend filtering
        return data
