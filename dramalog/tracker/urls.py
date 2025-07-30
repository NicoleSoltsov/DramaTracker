from rest_framework.routers import DefaultRouter
from .views import WatchStatusViewSet

router = DefaultRouter()
router.register(r'status', WatchStatusViewSet, basename='status')

urlpatterns = router.urls
