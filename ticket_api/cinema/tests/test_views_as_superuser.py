from datetime import date
from datetime import time

from hamcrest import all_of
from hamcrest import assert_that
from hamcrest import empty
from hamcrest import has_entries
from hamcrest import has_item
from hamcrest import has_length
from hamcrest import has_properties
from hamcrest import none
from hamcrest import not_
from rest_framework.status import HTTP_200_OK
from rest_framework.status import HTTP_201_CREATED
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.status import HTTP_403_FORBIDDEN
from rest_framework.status import HTTP_422_UNPROCESSABLE_ENTITY
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from ticket_api.cinema.tests.mixins import TicketSetupMixin
from ticket_api.cinema.tests.utils import is_page_of


class AdminAPITestCase(TicketSetupMixin, APITestCase):
    def setUp(self):
        super(AdminAPITestCase, self).setUp()

        refresh_token = RefreshToken.for_user(self.superuser)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(refresh_token.access_token),
        )

    def test_user_info(self):
        response = self.client.get('/api/user-info/')
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=has_entries(
                    email=self.superuser.email,
                    is_anonymous=False,
                    is_authenticated=True,
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

    def test_create_movie(self):
        response = self.client.post(
            '/api/movies/',
            data={
                'name': 'Avengers 4',
                'duration': 181,
            },
        )
        assert_that(
            response,
            has_properties(
                status_code=HTTP_201_CREATED,
                data=has_entries(
                    url=not_(empty()),
                    name='Avengers 4',
                    duration=181,
                ),
            ),
        )

    def test_get_movie(self):
        response = self.client.get(self.movie_90_url)
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=self.movie_90_match,
            )
        )

    def test_update_unused_movie(self):
        response = self.client.put(
            self.movie_unused_url,
            data={
                'name': 'Avengers 4',
                'duration': 181,
            },
        )
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=has_entries(
                    url=self.movie_unused_url_match,
                    name='Avengers 4',
                    duration=181,
                ),
            )
        )

    def test_prevents_updating_used_movie(self):
        response = self.client.put(
            self.movie_90_url,
            data={
                'name': 'Avengers 4',
                'duration': 181,
            },
        )
        assert_that(
            response,
            has_properties(status_code=HTTP_422_UNPROCESSABLE_ENTITY),
        )

    def test_remove_unused_movie(self):
        response = self.client.delete(self.movie_unused_url)
        assert_that(response, has_properties(status_code=HTTP_204_NO_CONTENT))

    def test_prevents_removing_used_movie(self):
        response = self.client.delete(self.movie_90_url)
        assert_that(
            response,
            has_properties(status_code=HTTP_422_UNPROCESSABLE_ENTITY),
        )

    def test_list_movie_sessions(self):
        response = self.client.get('/api/movie-sessions/')
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=is_page_of(
                    self.movie_session_past_match,
                    self.movie_session_100_90_match,
                    self.movie_session_400_120_match,
                    count=3,
                )
            )
        )

    def test_create_movie_session(self):
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
        assert_that(
            response,
            has_properties(
                status_code=HTTP_201_CREATED,
                data=has_entries(
                    url=not_(empty()),
                    hall=self.hall_100_url_match,
                    movie=self.movie_90_url_match,
                    date=not_(empty()),
                    starts_at=not_(empty()),
                    ticket_cost='150.00',
                    advertise_duration=15,
                )
            )
        )

    def test_prevents_creating_movie_session_after_day_end(self):
        response = self.client.post(
            '/api/movie-sessions/',
            data={
                'hall': self.hall_100_url,
                'movie': self.movie_120_url,
                'date': self.movie_session_past.date,
                'starts_at': time(23, 1),
                'ticket_cost': 200.0,
            }
        )
        assert_that(
            response,
            has_properties(status_code=HTTP_400_BAD_REQUEST),
        )

    def test_prevents_creating_movie_session_before_day_begining(self):
        response = self.client.post(
            '/api/movie-sessions/',
            data={
                'hall': self.hall_100_url,
                'movie': self.movie_120_url,
                'date': self.movie_session_past.date,
                'starts_at': time(7, 59),
                'ticket_cost': 200.0,
            }
        )
        assert_that(
            response,
            has_properties(status_code=HTTP_400_BAD_REQUEST),
        )

    def test_prevents_creating_overlapping_movie_session(self):
        response = self.client.post(
            '/api/movie-sessions/',
            data={
                'hall': self.hall_100_url,
                'movie': self.movie_120_url,
                'date': self.movie_session_past.date,
                'starts_at': self.movie_session_past.starts_at,
                'ticket_cost': 200.0,
            }
        )
        assert_that(
            response,
            has_properties(status_code=HTTP_422_UNPROCESSABLE_ENTITY),
        )

    def test_get_movie_session(self):
        response = self.client.get(self.movie_session_100_90_url)
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=self.movie_session_100_90_match,
            ),
        )

    def test_update_unused_movie_session(self):
        response = self.client.put(
            self.movie_session_past_url,
            data={
                'hall': self.hall_400_url,
                'movie': self.movie_120_url,
                'date': date(2019, 4, 20),
                'starts_at': time(12),
                'ticket_cost': '200.00',
                'advertise_duration': 20,
            },
        )
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=has_entries(
                    hall=self.hall_400_url_match,
                    movie=self.movie_120_url_match,
                    date=not_(empty()),
                    starts_at=not_(empty()),
                    ticket_cost='200.00',
                    advertise_duration=20,
                ),
            )
        )

    def test_prevents_updating_used_movie_session(self):
        response = self.client.put(
            self.movie_session_100_90_url,
            data={
                'hall': self.hall_100_url,
                'movie': self.movie_90_url,
                'date': date(2019, 4, 20),
                'starts_at': time(12),
                'ticket_cost': '200.00',
                'advertise_duration': 20,
            },
        )
        assert_that(
            response,
            has_properties(status_code=HTTP_422_UNPROCESSABLE_ENTITY),
        )

    def test_remove_unused_movie_session(self):
        response = self.client.delete(self.movie_session_past_url)
        assert_that(response, has_properties(status_code=HTTP_204_NO_CONTENT))

    def test_prevents_removing_used_movie_session(self):
        response = self.client.delete(self.movie_session_100_90_url)
        assert_that(
            response,
            has_properties(status_code=HTTP_422_UNPROCESSABLE_ENTITY),
        )

    def test_get_seats_schema(self):
        response = self.client.get(self.movie_session_100_90_url + 'seats/')
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=has_entries(
                    rows_number=self.movie_session_100_90.hall.rows_number,
                    seats_per_row=self.movie_session_100_90.hall.seats_per_row,
                    booked_seats=all_of(
                        has_length(1),
                        has_item(
                            has_entries(
                                row_number=5,
                                seat_number=5,
                            ),
                        )
                    )
                )
            )
        )

    def test_success_booking(self):
        response = self.client.post(
            self.movie_session_100_90_url + 'book_ticket/',
            data={
                'row_number': 3,
                'seat_number': 3,
            },
        )
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=has_entries(
                    movie_session=self.movie_session_100_90_url_match,
                    customer=self.superuser.email,
                    row_number=3,
                    seat_number=3,
                    cost=self.movie_session_100_90_cost_str,
                    booked_at=not_(empty()),
                    paid_at=none(),
                )
            )
        )

    def test_prevents_second_booking_on_same_seat(self):
        self.client.post(
            self.movie_session_100_90_url + 'book_ticket/',
            data={
                'row_number': 3,
                'seat_number': 3,
            }
        )

        response = self.client.post(
            self.movie_session_100_90_url + 'book_ticket/',
            data={
                'row_number': 3,
                'seat_number': 3,
            }
        )
        assert_that(
            response,
            has_properties(status_code=HTTP_422_UNPROCESSABLE_ENTITY),
        )

    def test_prevents_booking_out_of_booking_period(self):
        response = self.client.post(
            self.movie_session_past_url + 'book_ticket/',
            data={
                'row_number': 3,
                'seat_number': 3,
            }
        )

        assert_that(
            response,
            has_properties(status_code=HTTP_422_UNPROCESSABLE_ENTITY),
        )

    def test_success_booking_for_customer(self):
        response = self.client.post(
            self.movie_session_100_90_url + 'book_ticket_for_customer/',
            data={
                'customer': self.user_2.email,
                'row_number': 1,
                'seat_number': 1,
            },
        )
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=has_entries(
                    movie_session=self.movie_session_100_90_url_match,
                    customer=self.user_2.email,
                    row_number=1,
                    seat_number=1,
                    cost=self.movie_session_100_90_cost_str,
                    booked_at=not_(empty()),
                    paid_at=none(),
                )
            )
        )

    def test_list_tickets(self):
        response = self.client.get('/api/tickets/')
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=is_page_of(
                    self.ticket_100_90_match,
                    self.ticket_400_120_match,
                    count=2,
                ),
            )
        )

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

    def test_get_tickets(self):
        response = self.client.get(self.ticket_100_90_url)
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=self.ticket_100_90_match,
            )
        )

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

    def test_remove_tickets(self):
        response = self.client.delete(self.ticket_100_90_url)
        assert_that(response, has_properties(status_code=HTTP_403_FORBIDDEN))

    def test_pay(self):
        response = self.client.post(self.ticket_100_90_url + 'pay/')
        assert_that(
            response,
            has_properties(
                status_code=HTTP_200_OK,
                data=self.ticket_100_90_match,
            )
        )

    def test_prevents_paying_twice(self):
        self.client.post(self.ticket_100_90_url + 'pay/')

        response = self.client.post(self.ticket_100_90_url + 'pay/')
        assert_that(response, has_properties(status_code=422))

    def test_cancel(self):
        response = self.client.post(self.ticket_100_90_url + 'cancel/')
        assert_that(response, has_properties(status_code=HTTP_204_NO_CONTENT))

    def test_prevents_canceling_paid(self):
        self.client.post(self.ticket_100_90_url + 'pay/')

        response = self.client.post(self.ticket_100_90_url + 'cancel/')
        assert_that(response, has_properties(status_code=422))
