from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DramaViewSet, add_kdrama_by_name, GenreListCreateView, MoodListCreateView

router = DefaultRouter()
router.register(r'dramas', DramaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('kdramas/add-by-name/', add_kdrama_by_name), 
    path('genres/', GenreListCreateView.as_view(), name='genre-list-create'),
    path('moods/', MoodListCreateView.as_view(), name='mood-list-create'), 
]
