# tracker/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import WatchStatus
from .serializers import WatchStatusSerializer

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
        # ensure serializer has request in context (for queryset scoping)
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
