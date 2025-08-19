from rest_framework import viewsets, filters, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes, action
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from django.db.models import Q, Exists, OuterRef, Subquery, Value, DateTimeField
from django.db.models.functions import Coalesce, Greatest

from .models import *
from .serializers import DramaSerializer, GenreSerializer, MoodSerializer
from .tmdb_utils import search_kdrama, search_kdrama_candidates, fetch_kdrama_by_tmdb_id, get_tv_seasons
from .spotify_utils import get_ost_playlist_url

# Cross-app models for filters/annotations
from tracker.models import WatchStatus
from reviews.models import Review


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
        """
        Query params supported:

          search=<str>                 (DRF SearchFilter on 'title')

          status=plan,watching,on_hold,dropped,finished   (from tracker.WatchStatus; comma-separated)
          genre=Romance,Thriller                           (by Genre.name; comma-separated)
          length=short|medium|long                         (<=12, 13–24, >=25 episodes)
          year_decade=2020s|2010s|2000s
          year_from=<int>&year_to=<int>
          has_review=true|false                            (Review by YOU exists?)

          my_rating_order=asc|desc                         (order by your Review.rating)
          order=updated|created|title                      (fallback order when my_rating_order not set)
                - updated => most recently updated, defined as the max of:
                              WatchStatus.updated_at (yours) and Review.updated_at (yours).
                - created => newest first by id (since Drama has no created field)
                - title   => title A→Z
        """
        user = self.request.user

        qs = (
            Drama.objects
            .filter(user=user)
            .prefetch_related('genres')
        )

        # --- Subqueries/annotations from other apps (scoped to current user) ---

        # Your WatchStatus per (user, drama)
        ws_sub = WatchStatus.objects.filter(user=user, drama=OuterRef('pk'))
        latest_ws_dt = Subquery(ws_sub.values('updated_at')[:1])

        # Your latest review (if any)
        rv_sub = Review.objects.filter(user=user, drama=OuterRef('pk')).order_by('-updated_at')
        latest_rv_dt = Subquery(rv_sub.values('updated_at')[:1])
        my_rating_sub = Subquery(rv_sub.values('rating')[:1])

        # Coerce NULLs so Greatest() works predictably
        very_old = Value("1970-01-01T00:00:00Z", output_field=DateTimeField())

        qs = qs.annotate(
            has_review=Exists(Review.objects.filter(user=user, drama=OuterRef('pk'))),
            my_rating=my_rating_sub,
            latest_update=Greatest(
                Coalesce(latest_ws_dt, very_old),
                Coalesce(latest_rv_dt, very_old),
            ),
        )

        params = self.request.query_params

        # ---- Filters ----

        # Watch status (via tracker.WatchStatus)
        statuses = (params.get('status') or '').strip()
        if statuses:
            wanted = [s.strip() for s in statuses.split(',') if s.strip()]
            qs = qs.filter(
                Exists(
                    WatchStatus.objects.filter(
                        user=user,
                        drama=OuterRef('pk'),
                        status__in=wanted,
                    )
                )
            )

        # Genre names (comma-separated)
        genre_names = (params.get('genre') or '').strip()
        if genre_names:
            wanted = [g.strip() for g in genre_names.split(',') if g.strip()]
            qs = qs.filter(genres__name__in=wanted).distinct()

        # Length buckets by total_episodes
        length = (params.get('length') or '').strip().lower()
        if length == 'short':
            qs = qs.filter(total_episodes__lte=12)
        elif length == 'medium':
            qs = qs.filter(total_episodes__gte=13, total_episodes__lte=24)
        elif length == 'long':
            qs = qs.filter(total_episodes__gte=25)

        # Release decade or explicit range
        decade = (params.get('year_decade') or '').strip().lower()
        if decade.endswith('s') and len(decade) == 5 and decade[:4].isdigit():
            base = int(decade[:4])
            qs = qs.filter(release_year__gte=base, release_year__lte=base + 9)

        year_from = params.get('year_from')
        year_to = params.get('year_to')
        if year_from and year_from.isdigit():
            qs = qs.filter(release_year__gte=int(year_from))
        if year_to and year_to.isdigit():
            qs = qs.filter(release_year__lte=int(year_to))

        # Has review?
        has_review = (params.get('has_review') or '').strip().lower()
        if has_review in ('true', 'false'):
            qs = qs.filter(has_review=(has_review == 'true'))

        # ---- Ordering ----

        my_rating_order = (params.get('my_rating_order') or '').strip().lower()
        if my_rating_order in ('asc', 'desc'):
            qs = qs.order_by(('-' if my_rating_order == 'desc' else '') + 'my_rating', '-latest_update', '-id')
        else:
            order = (params.get('order') or 'updated').strip().lower()
            if order == 'title':
                qs = qs.order_by('title')
            elif order == 'created':
                qs = qs.order_by('-id')  # Drama has no created_at; newest first by PK
            else:
                # default: most recently updated (watch progress or your review)
                qs = qs.order_by('-latest_update', '-id')

        return qs

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


# ---------- Seasons endpoints ----------

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
