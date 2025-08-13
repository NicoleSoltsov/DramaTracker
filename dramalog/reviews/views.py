from rest_framework import viewsets, permissions
from .models import Review
from .serializers import ReviewSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = (
            Review.objects
            .filter(user=self.request.user)
            .select_related('drama')
        )

        # Optional: filter by tmdb_id if provided
        tmdb = self.request.query_params.get('drama_tmdb_id')
        if tmdb and str(tmdb).isdigit():
            qs = qs.filter(drama__tmdb_id=int(tmdb))

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
