from rest_framework.routers import DefaultRouter
from .views import WatchStatusViewSet, JournalEntryViewSet

router = DefaultRouter()
router.register(r'status', WatchStatusViewSet, basename='status')
router.register(r'journals', JournalEntryViewSet, basename='journals')  # NEW

urlpatterns = router.urls
