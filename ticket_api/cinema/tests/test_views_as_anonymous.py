from datetime import date
from datetime import time

from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import has_item
from hamcrest import has_properties
from hamcrest import not_
from rest_framework.status import HTTP_200_OK
from rest_framework.status import HTTP_403_FORBIDDEN
from rest_framework.test import APITestCase

from ticket_api.cinema.tests.mixins import TicketSetupMixin
from ticket_api.cinema.tests.utils import is_page_of


class AnonymousAPITestCase(TicketSetupMixin, APITestCase):
    def setUp(self):
        super(AnonymousAPITestCase, self).setUp()

        self.client.force_authenticate(None)

    def test_user_info(self):
        response = self.client.get('/api/user-info/')
        assert_that(
            response,
            has_properties(
                status_code=200,
                data=has_entries(
                    is_anonymous=True,
                    is_authenticated=False,
                )
            )
        )

    def test_list_halls(self):
        response = self.client.get('/api/halls/')
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=is_page_of(
                    self.hall_100_match,
                    self.hall_400_match,
                    count=6,
                )
            )
        )

    def test_prevents_creating_hall(self):
        response = self.client.post(
            '/api/halls/',
            data={
                'name': 'Sun',
                'rows_number': 5,
                'seats_per_row': 8,
                'cleaning_duration': 5,
            },
        )
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_get_hall(self):
        response = self.client.get(self.hall_100_url)
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=self.hall_100_match,
            )
        )

    def test_prevents_updating_hall(self):
        response = self.client.put(
            self.hall_100_url,
            data={
                'name': 'Sun',
                'rows_number': 5,
                'seats_per_row': 8,
                'cleaning_duration': 5,
            },
        )
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_removing_hall(self):
        response = self.client.delete(self.hall_100_url)
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_list_movies(self):
        response = self.client.get('/api/movies/')
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=is_page_of(
                    self.movie_unused_match,
                    self.movie_90_match,
                    self.movie_120_match,
                    count=3,
                )
            )
        )

    def test_prevents_creating_movie(self):
        response = self.client.post(
            '/api/movies/',
            data={
                'name': 'Avengers 4',
                'duration': 181,
            },
        )
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_get_movie(self):
        response = self.client.get(self.movie_90_url)
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=self.movie_90_match,
            )
        )

    def test_prevents_updating_movie(self):
        response = self.client.put(
            self.movie_90_url,
            data={
                'name': 'Avengers 4',
                'duration': 181,
            },
        )
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_removing_movie(self):
        response = self.client.delete(self.movie_90_url)
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_list_movie_sessions(self):
        response = self.client.get('/api/movie-sessions/')
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=is_page_of(
                    self.movie_session_100_90_match,
                    self.movie_session_400_120_match,
                    count=2,
                )
            )
        )

    def test_list_movies_sessions_without_past(self):
        response = self.client.get('/api/movie-sessions/')
        assert_that(
            response,
            has_properties(
                data=has_entries(
                    results=not_(has_item(self.movie_session_past_match))
                )
            )
        )

    def test_prevents_creating_movie_session(self):
        response = self.client.post(
            '/api/movie-sessions/',
            data={
                'hall': self.hall_100_url,
                'movie': self.movie_90_url,
                'date': date(2019, 4, 20),
                'starts_at': time(12),
                'ticket_cost': 150,
                'advertise_duration': 15,
            },
        )
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_get_movie_session(self):
        response = self.client.get(self.movie_session_100_90_url)
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=self.movie_session_100_90_match,
            ),
        )

    def test_prevents_updating_movie_session(self):
        response = self.client.put(
            self.movie_session_100_90_url,
            data={
                'hall': self.hall_100_url,
                'movie': self.movie_90_url,
                'date': date(2019, 4, 20),
                'starts_at': time(12),
                'ticket_cost': '150.00',
                'advertise_duration': 15,
            },
        )
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_removing_movie_session(self):
        response = self.client.delete(self.movie_session_100_90_url)
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_getting_seats_schema(self):
        response = self.client.get(self.movie_session_100_90_url + 'seats/')
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_booking_for_itself(self):
        response = self.client.post(
            self.movie_session_100_90_url + 'book_ticket/',
            data={
                'row_number': 1,
                'seat_number': 1,
            },
        )
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_booking_for_customer(self):
        response = self.client.post(
            self.movie_session_100_90_url + 'book_ticket_for_customer/',
            data={
                'customer': self.user_1.email,
                'row_number': 1,
                'seat_number': 1,
            },
        )
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_listing_tickets(self):
        response = self.client.get('/api/tickets/')
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_creating_tickets(self):
        response = self.client.post(
            '/api/tickets/',
            data={
                'movie_session': self.movie_session_100_90_url,
                'customer': self.user_1.email,
                'row_number': 1,
                'seat_number': 1,
                'cost': '150.00',
            },
        )
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_getting_tickets(self):
        response = self.client.get(self.ticket_100_90_url)
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_update_tickets(self):
        response = self.client.post(
            self.ticket_100_90_url,
            data={
                'movie_session': self.movie_session_100_90_url,
                'customer': self.user_1.email,
                'row_number': 1,
                'seat_number': 1,
                'cost': '150.00',
            },
        )
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_removing_tickets(self):
        response = self.client.delete(self.ticket_100_90_url)
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_paying(self):
        response = self.client.post(self.ticket_100_90_url + 'pay/')
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_prevents_canceling(self):
        response = self.client.post(self.ticket_100_90_url + 'cancel/')
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))
