from rest_framework import viewsets
from .models import Drama
from .serializers import DramaSerializer

class DramaViewSet(viewsets.ModelViewSet):
    queryset = Drama.objects.all()
    serializer_class = DramaSerializer
