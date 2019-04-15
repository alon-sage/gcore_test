from datetime import time
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from hamcrest import ends_with
from hamcrest import has_entries

from ticket_api.cinema.models import Hall
from ticket_api.cinema.models import Movie
from ticket_api.cinema.models import MovieSession
from ticket_api.cinema.models import User


def make_url_of_model(instance):
    model = type(instance)
    view_name = model._meta.object_name.lower() + '-detail'
    return reverse(view_name, args=(instance.id,))


class UserSetupMixin:
    def setUp(self):
        super(UserSetupMixin, self).setUp()

        self.user_password = 'HAASD576esdea54se4EDA'
        self.user_1 = User.objects.create(
            email='user_1@example.com',
            password=self.user_password,
        )
        self.user_2 = User.objects.create(
            email='user_2@example.com',
            password=self.user_password,
        )
        self.superuser_password = 'HAASD576esdea54se4VODA'
        self.superuser = User.objects.create_superuser(
            email='superuser@example.com',
            password=self.superuser_password,
        )


class HallSetupMixin:
    def setUp(self):
        super(HallSetupMixin, self).setUp()

        self.hall_100 = Hall.objects.create(
            name='Hall 100',
            rows_number=10,
            seats_per_row=10,
        )
        self.hall_100_url = make_url_of_model(self.hall_100)
        self.hall_100_url_match = ends_with(self.hall_100_url)
        self.hall_100_match = has_entries(
            url=self.hall_100_url_match,
            name='Hall 100',
            rows_number=10,
            seats_per_row=10,
            capacity=100,
        )

        self.hall_400 = Hall.objects.create(
            name='Hall 400',
            rows_number=20,
            seats_per_row=20,
        )
        self.hall_400_url = make_url_of_model(self.hall_400)
        self.hall_400_url_match = ends_with(self.hall_400_url)
        self.hall_400_match = has_entries(
            url=self.hall_400_url_match,
            name='Hall 400',
            rows_number=20,
            seats_per_row=20,
            capacity=400,
        )


class MovieSetupMixin:
    def setUp(self):
        super(MovieSetupMixin, self).setUp()

        self.movie_unused = Movie.objects.create(
            name='The Disaster Artist',
            duration=104,
        )
        self.movie_unused_url = make_url_of_model(self.movie_unused)
        self.movie_unused_url_match = ends_with(self.movie_unused_url)
        self.movie_unused_match = has_entries(
            url=self.movie_unused_url_match,
            name='The Disaster Artist',
            duration=104,
        )

        self.movie_90 = Movie.objects.create(name='Movie 90', duration=90)
        self.movie_90_url = make_url_of_model(self.movie_90)
        self.movie_90_url_match = ends_with(self.movie_90_url)
        self.movie_90_match = has_entries(
            url=self.movie_90_url_match,
            name='Movie 90',
            duration=90,
        )

        self.movie_120 = Movie.objects.create(name='Movie 120', duration=120)
        self.movie_120_url = make_url_of_model(self.movie_120)
        self.movie_120_url_match = ends_with(self.movie_120_url)
        self.movie_120_match = has_entries(
            url=self.movie_120_url_match,
            name='Movie 120',
            duration=120,
        )


class MovieSessionSetupMixin(HallSetupMixin, MovieSetupMixin):
    def setUp(self):
        super(MovieSessionSetupMixin, self).setUp()

        self.movie_session_past = MovieSession.objects.create(
            hall=self.hall_100,
            movie=self.movie_90,
            date=(timezone.now() - timedelta(days=1)).date(),
            starts_at=time(8),
            ticket_cost=100.0,
        )
        self.movie_session_past_cost_str = '100.00'
        self.movie_session_past_url = make_url_of_model(self.movie_session_past)
        self.movie_session_past_url_match = ends_with(
            self.movie_session_past_url,
        )
        self.movie_session_past_match = has_entries(
            url=self.movie_session_past_url_match,
            hall=self.hall_100_url_match,
            movie=self.movie_90_url_match,
        )

        self.movie_session_100_90 = MovieSession.objects.create(
            hall=self.hall_100,
            movie=self.movie_90,
            date=(timezone.now() + timedelta(days=1)).date(),
            starts_at=time(8),
            ticket_cost=100.0,
        )
        self.movie_session_100_90_cost_str = '100.00'
        self.movie_session_100_90_url = make_url_of_model(
            self.movie_session_100_90,
        )
        self.movie_session_100_90_url_match = ends_with(
            self.movie_session_100_90_url,
        )
        self.movie_session_100_90_match = has_entries(
            url=self.movie_session_100_90_url_match,
            hall=self.hall_100_url_match,
            movie=self.movie_90_url_match,
        )

        self.movie_session_400_120 = MovieSession.objects.create(
            hall=self.hall_400,
            movie=self.movie_120,
            date=(timezone.now() + timedelta(days=1)).date(),
            starts_at=time(12),
            ticket_cost=150,
        )
        self.movie_session_400_120_cost_str = '150.00'
        self.movie_session_400_120_url = make_url_of_model(
            self.movie_session_400_120,
        )
        self.movie_session_400_120_url_match = ends_with(
            self.movie_session_400_120_url,
        )
        self.movie_session_400_120_match = has_entries(
            url=self.movie_session_400_120_url_match,
            hall=self.hall_400_url_match,
            movie=self.movie_120_url_match,
        )


class TicketSetupMixin(UserSetupMixin, MovieSessionSetupMixin):
    def setUp(self):
        super(TicketSetupMixin, self).setUp()

        self.ticket_100_90 = self.movie_session_100_90.book_ticket(
            self.user_1,
            row_number=5,
            seat_number=5,
        )
        self.ticket_100_90_url = make_url_of_model(self.ticket_100_90)
        self.ticket_100_90_url_match = ends_with(self.ticket_100_90_url)
        self.ticket_100_90_match = has_entries(
            url=self.ticket_100_90_url_match,
        )

        self.ticket_400_120 = self.movie_session_400_120.book_ticket(
            self.user_1,
            row_number=10,
            seat_number=10,
        )
        self.ticket_400_120_url = make_url_of_model(self.ticket_400_120)
        self.ticket_400_120_url_match = ends_with(self.ticket_400_120_url)
        self.ticket_400_120_match = has_entries(
            url=self.ticket_400_120_url_match,
        )
