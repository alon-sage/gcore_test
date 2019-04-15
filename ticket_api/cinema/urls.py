from rest_framework.routers import DefaultRouter

from ticket_api.cinema.views import HallViewSet
from ticket_api.cinema.views import MovieSessionViewSet
from ticket_api.cinema.views import MovieViewSet
from ticket_api.cinema.views import TicketViewSet
from ticket_api.cinema.views import UserInfoViewSet
from ticket_api.cinema.views import UserViewSet

router = DefaultRouter()
router.register(r'user-info', UserInfoViewSet, base_name='user-info')
router.register(r'users', UserViewSet)
router.register(r'halls', HallViewSet)
router.register(r'movies', MovieViewSet)
router.register(r'movie-sessions', MovieSessionViewSet)
router.register(r'tickets', TicketViewSet)

urlpatterns = router.urls
