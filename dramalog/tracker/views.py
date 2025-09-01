# tracker/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import WatchStatus, JournalEntry
from .serializers import WatchStatusSerializer, JournalEntrySerializer

class WatchStatusViewSet(viewsets.ModelViewSet):
    serializer_class = WatchStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = WatchStatus.objects.filter(user=self.request.user)
        drama_id = self.request.query_params.get("drama_id")
        if drama_id:
            try:
                qs = qs.filter(drama__tmdb_id=int(drama_id))  # tmdb_id query filter
            except (TypeError, ValueError):
                pass
        return qs

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", {})
        kwargs["context"]["request"] = self.request
        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        drama = serializer.validated_data["drama"]  # Drama instance

        defaults = {
            "status": serializer.validated_data.get("status"),
            "current_season": serializer.validated_data.get("current_season", 1),
            "current_episode": serializer.validated_data.get("current_episode", 0),
            "rewatch_count": serializer.validated_data.get("rewatch_count", 0),
            "personal_rating": serializer.validated_data.get("personal_rating"),
        }

        obj, created = WatchStatus.objects.update_or_create(
            user=user, drama=drama, defaults=defaults
        )

        out = self.get_serializer(obj)
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=code, headers=headers)

# NEW
class JournalEntryViewSet(viewsets.ModelViewSet):
    """
    CRUD for per-episode journal entries.
    Filters:
      - ?drama_tmdb_id=1234
      - ?season=1
      - ?episode=5
    Ordered newest first.
    """
    serializer_class = JournalEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = JournalEntry.objects.filter(user=self.request.user).select_related("drama", "watch_status")
        tmdb = self.request.query_params.get("drama_tmdb_id")
        season = self.request.query_params.get("season")
        episode = self.request.query_params.get("episode")

        if tmdb:
            try:
                qs = qs.filter(drama__tmdb_id=int(tmdb))
            except (TypeError, ValueError):
                pass
        if season:
            try:
                qs = qs.filter(season=int(season))
            except (TypeError, ValueError):
                pass
        if episode:
            try:
                qs = qs.filter(episode=int(episode))
            except (TypeError, ValueError):
                pass
        return qs.order_by("-created_at")

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", {})
        kwargs["context"]["request"] = self.request
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
