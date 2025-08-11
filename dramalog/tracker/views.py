from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import WatchStatus
from .serializers import WatchStatusSerializer

class WatchStatusViewSet(viewsets.ModelViewSet):
    serializer_class = WatchStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Always start with the user's records
        qs = WatchStatus.objects.filter(user=self.request.user)

        # Optional filter by drama title (for your frontend progress tracker)
        drama_title = self.request.query_params.get("drama")
        if drama_title:
            qs = qs.filter(drama__title=drama_title)

        # Optional filter by drama ID if you ever send ?drama_id=
        drama_id = self.request.query_params.get("drama_id")
        if drama_id:
            qs = qs.filter(drama__id=drama_id)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
