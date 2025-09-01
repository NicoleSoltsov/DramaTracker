# tracker/serializers.py
from rest_framework import serializers
from .models import WatchStatus, JournalEntry
from dramas.models import Drama

class WatchStatusSerializer(serializers.ModelSerializer):
    # Use tmdb_id to identify the drama, but only from THIS user
    drama = serializers.SlugRelatedField(
        slug_field='tmdb_id',
        queryset=Drama.objects.none()
    )

    class Meta:
        model = WatchStatus
        fields = '__all__'   # now includes current_season automatically
        read_only_fields = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        req = self.context.get('request')
        if req and req.user and req.user.is_authenticated:
            self.fields['drama'].queryset = Drama.objects.filter(user=req.user)

    def validate(self, attrs):
        # small sanity checks
        rating = attrs.get("personal_rating", None)
        if rating is not None and not (1 <= rating <= 10):
            raise serializers.ValidationError({"personal_rating": "Must be between 1 and 10."})
        if attrs.get("current_season", 1) < 1:
            raise serializers.ValidationError({"current_season": "Must be >= 1."})
        # episode can be zero to indicate "not started" for a season
        if attrs.get("current_episode", 0) < 0:
            raise serializers.ValidationError({"current_episode": "Must be >= 0."})
        return attrs

# NEW
class JournalEntrySerializer(serializers.ModelSerializer):
    # allow client to post by tmdb_id; we’ll resolve to Drama & WatchStatus
    drama = serializers.SlugRelatedField(slug_field="tmdb_id", queryset=Drama.objects.none())
    # read-only username for display
    user_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id", "user", "user_display", "drama",
            "season", "episode", "title", "content",
            "watch_status", "created_at", "updated_at",
        ]
        read_only_fields = ["user", "watch_status", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        req = self.context.get('request')
        if req and req.user and req.user.is_authenticated:
            self.fields['drama'].queryset = Drama.objects.filter(user=req.user)

    def get_user_display(self, obj):
        return getattr(obj.user, "username", None)

    def validate(self, attrs):
        if attrs.get("season", 1) < 1:
            raise serializers.ValidationError({"season": "Must be >= 1."})
        if attrs.get("episode", 1) < 1:
            raise serializers.ValidationError({"episode": "Must be >= 1."})
        return attrs

    def create(self, validated_data):
        """
        Auto-attach user and watch_status (create WatchStatus if missing).
        """
        request = self.context.get("request")
        user = request.user
        drama = validated_data["drama"]
        season = validated_data.get("season", 1)
        episode = validated_data.get("episode", 1)

        # ensure a WatchStatus exists for this user/drama
        ws, _ = WatchStatus.objects.get_or_create(
            user=user,
            drama=drama,
            defaults={"status": "watching", "current_season": season, "current_episode": 0}
        )
        # optional: bump progress if journaled beyond current episode in same season
        if ws.current_season == season and episode > ws.current_episode:
            ws.current_episode = episode
            ws.save(update_fields=["current_episode", "updated_at"])

        entry = JournalEntry.objects.create(
            user=user,
            drama=drama,
            watch_status=ws,
            season=season,
            episode=episode,
            title=validated_data.get("title", ""),
            content=validated_data.get("content", ""),
        )
        return entry
