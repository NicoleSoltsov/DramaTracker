from rest_framework import viewsets, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from .models import *
from .serializers import DramaSerializer, GenreSerializer, MoodSerializer
from .tmdb_utils import search_kdrama  
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .spotify_utils import get_ost_playlist_url



class GenreListCreateView(generics.ListCreateAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

class MoodListCreateView(generics.ListCreateAPIView):
    queryset = Mood.objects.all()
    serializer_class = MoodSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

class DramaViewSet(viewsets.ModelViewSet):
    queryset = Drama.objects.all()
    serializer_class = DramaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    search_fields = ['title']
    filter_backends = [filters.SearchFilter]

    def get_queryset(self):
        return Drama.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_filter_backends(self):
        """Only apply search filter on list view, not detail view."""
        if self.action == 'list':
            return [filters.SearchFilter]
        return []



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
        return Response({"error": "Drama not found"}, status=status.HTTP_404_NOT_FOUND)
    
    OST_playlist = get_ost_playlist_url(kdrama_data["title"])

    # Create the new drama object
    drama = Drama.objects.create(
        user=request.user,
        title=kdrama_data["title"],
        description=kdrama_data["description"],
        poster_url=kdrama_data["poster_url"], 
        release_year=int(kdrama_data["release_year"]),
        total_episodes=kdrama_data["total_episodes"],
        OST_playlist=OST_playlist
    )

    # Add genres from TMDB
    genre_names = kdrama_data.get("genre_names", [])
    for name in genre_names:
        genre, _ = Genre.objects.get_or_create(name=name)
        drama.genres.add(genre)

    # Return serialized drama
    serializer = DramaSerializer(drama)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
