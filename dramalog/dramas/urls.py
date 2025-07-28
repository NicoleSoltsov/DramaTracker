from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DramaViewSet

router = DefaultRouter()
router.register(r'dramas', DramaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
