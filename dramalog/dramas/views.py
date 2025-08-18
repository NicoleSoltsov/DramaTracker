from rest_framework import viewsets, filters
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from .models import *
from rest_framework.decorators import action   # <-- needed for @action
from django.db.models import Q  
from .serializers import DramaSerializer, GenreSerializer, MoodSerializer
from .tmdb_utils import search_kdrama, search_kdrama_candidates, fetch_kdrama_by_tmdb_id, get_tv_seasons
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
    
    @action(detail=False, methods=["POST"], url_path="bulk-delete")
    def bulk_delete(self, request):
        ids = request.data.get("ids") or []
        tmdb_ids = request.data.get("tmdb_ids") or []

        if not isinstance(ids, list) or not isinstance(tmdb_ids, list):
            return Response({"error": "`ids` and `tmdb_ids` must be lists."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not ids and not tmdb_ids:
            return Response({"error": "Provide at least one of `ids` or `tmdb_ids`."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Only delete the current user's dramas
        base_qs = Drama.objects.filter(user=request.user)

        q = Q()
        if ids:
            q |= Q(id__in=ids)
        if tmdb_ids:
            q |= Q(tmdb_id__in=tmdb_ids)

        to_delete = base_qs.filter(q).distinct()
        count = to_delete.count()
        to_delete.delete()

        return Response({"deleted": count}, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_filter_backends(self):
        """Only apply search filter on list view, not detail view."""
        if self.action == 'list':
            return [filters.SearchFilter]
        return []
    

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def add_kdrama_by_name(request):
    title = (request.data.get('title') or '').strip()
    tmdb_id = request.data.get('tmdb_id')

    if not title and not tmdb_id:
        return Response({"error": "No title or tmdb_id provided"}, status=status.HTTP_400_BAD_REQUEST)

    # 1) Resolve kdrama_data (prefer exact TMDB id)
    kdrama_data = None
    if tmdb_id:
        try:
            tmdb_id = int(tmdb_id)
        except (TypeError, ValueError):
            return Response({"error": "Invalid tmdb_id"}, status=status.HTTP_400_BAD_REQUEST)
        kdrama_data = fetch_kdrama_by_tmdb_id(tmdb_id)

    if not kdrama_data:
        # fallback to title search if ID was missing/failed
        if not title:
            return Response({"error": "Title required when tmdb_id lookup fails"}, status=status.HTTP_400_BAD_REQUEST)
        kdrama_data = search_kdrama(title)

    if not kdrama_data:
        return Response({"error": "Drama not found"}, status=status.HTTP_404_NOT_FOUND)

    # 2) Per-user duplicate check (by tmdb_id if available, else fall back to title)
    existing = None
    if kdrama_data.get("tmdb_id"):
        existing = Drama.objects.filter(user=request.user, tmdb_id=kdrama_data["tmdb_id"]).first()
    elif title:
        existing = Drama.objects.filter(user=request.user, title__iexact=kdrama_data["title"]).first()

    if existing:
        return Response({"error": "You've already added this drama."}, status=status.HTTP_400_BAD_REQUEST)

    # 3) Best-effort OST lookup (must not fail creation)
    try:
        ost_url = get_ost_playlist_url(kdrama_data["title"])
    except Exception:
        ost_url = None

    # 4) Parse year safely
    try:
        release_year = int(kdrama_data.get("release_year")) if kdrama_data.get("release_year") else None
    except (TypeError, ValueError):
        release_year = None

    # 5) Create Drama
    drama = Drama.objects.create(
        user=request.user,
        title=kdrama_data.get("title") or title,
        description=kdrama_data.get("description") or "",
        poster_url=kdrama_data.get("poster_url"),
        release_year=release_year,
        total_episodes=kdrama_data.get("total_episodes") or 0,
        tmdb_id=kdrama_data.get("tmdb_id"),
        OST_playlist=ost_url,
    )

    # 6) Attach genres
    for name in kdrama_data.get("genre_names", []):
        if not name:
            continue
        genre, _ = Genre.objects.get_or_create(name=name)
        drama.genres.add(genre)

    return Response(DramaSerializer(drama).data, status=status.HTTP_201_CREATED)

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def kdrama_search(request):
    q = (request.query_params.get("q") or "").strip()
    if not q:
        return Response([], status=status.HTTP_200_OK)
    try:
        results = search_kdrama_candidates(q, limit=8)
        return Response(results, status=status.HTTP_200_OK)
    except Exception:
        return Response({"detail": "TMDB search failed"}, status=status.HTTP_502_BAD_GATEWAY)

# ---------- NEW: Seasons endpoints ----------

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def seasons_by_tmdb_id(request):
    """
    GET /api/tmdb/seasons/?tmdb_id=61611
    Returns: {"tmdb_id": 61611, "seasons": [{season_number, episode_count, ...}, ...]}
    """
    tmdb_id = request.query_params.get("tmdb_id")
    if not tmdb_id:
        return Response({"error": "tmdb_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        tmdb_id = int(tmdb_id)
    except ValueError:
        return Response({"error": "tmdb_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        seasons = get_tv_seasons(tmdb_id)
        seasons = sorted(seasons, key=lambda s: s.get("season_number") or 0)
        return Response({"tmdb_id": tmdb_id, "seasons": seasons}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def seasons_by_drama_pk(request, pk: int):
    """
    GET /api/dramas/<pk>/seasons/
    Uses Drama.tmdb_id to fetch TMDB seasons.
    """
    try:
        drama = Drama.objects.get(pk=pk, user=request.user)
    except Drama.DoesNotExist:
        return Response({"error": "Drama not found"}, status=status.HTTP_404_NOT_FOUND)

    if not drama.tmdb_id:
        return Response({"error": "Drama has no tmdb_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        seasons = get_tv_seasons(drama.tmdb_id)
        seasons = sorted(seasons, key=lambda s: s.get("season_number") or 0)
        return Response({"drama_id": drama.pk, "tmdb_id": drama.tmdb_id, "seasons": seasons}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
