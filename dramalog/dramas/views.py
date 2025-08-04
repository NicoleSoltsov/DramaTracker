from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Drama
from .serializers import DramaSerializer
from .tmdb_utils import search_kdrama  
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication


class DramaViewSet(viewsets.ModelViewSet):
    queryset = Drama.objects.all()
    serializer_class = DramaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
def add_kdrama_by_name(request):
    title = request.data.get('title')
    if not title:
        return Response({"error": "No title provided"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if this user already posted the drama
    existing_drama = Drama.objects.filter(user=request.user, title__iexact=title).first()
    if existing_drama:
        return Response({"error": "You've already added this drama."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch data from TMDB
    kdrama_data = search_kdrama(title)
    if not kdrama_data:
        return Response({"error": "K-drama not found"}, status=status.HTTP_404_NOT_FOUND)

    # Create new drama with the user
    drama = Drama.objects.create(
        user=request.user,
        title=kdrama_data["title"],
        description=kdrama_data["description"],
        release_year=int(kdrama_data["release_year"]),
        total_episodes=kdrama_data["total_episodes"],
    )

    # Return the created drama as JSON
    serializer = DramaSerializer(drama)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

