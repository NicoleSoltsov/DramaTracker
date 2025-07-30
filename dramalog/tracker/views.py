from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import WatchStatus
from .serializers import WatchStatusSerializer
from rest_framework.permissions import IsAuthenticated

class WatchStatusViewSet(viewsets.ModelViewSet):
    serializer_class = WatchStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WatchStatus.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
