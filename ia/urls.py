from rest_framework.routers import DefaultRouter
from .views import ConversacionViewSet

router = DefaultRouter()
router.register(
    "conversaciones",
    ConversacionViewSet,
    basename="conversaciones"
)

urlpatterns = router.urls