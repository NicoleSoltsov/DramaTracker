from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DramaViewSet, add_kdrama_by_name

router = DefaultRouter()
router.register(r'dramas', DramaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('kdramas/add-by-name/', add_kdrama_by_name),  
]
