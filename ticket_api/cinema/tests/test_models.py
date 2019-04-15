from contextlib import ExitStack
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.test import TestCase
from hamcrest import assert_that
from hamcrest import calling
from hamcrest import raises

from ticket_api.cinema.exceptions import AttemptsIsOverError
from ticket_api.cinema.exceptions import NoBookingAvailableError
from ticket_api.cinema.exceptions import SeatNotAvailableError
from ticket_api.cinema.exceptions import TicketAlreadyPaidError
from ticket_api.cinema.models import OrderNumberGenerator
from ticket_api.cinema.models import Ticket
from ticket_api.cinema.tests.mixins import MovieSessionSetupMixin
from ticket_api.cinema.tests.mixins import TicketSetupMixin
from ticket_api.cinema.tests.mixins import UserSetupMixin


class OrderNumberGeneratorTestCase(TestCase):
    def test_attempts_limits(self):
        generator = OrderNumberGenerator(4, 8)
        with ExitStack() as stack:
            generate = stack.enter_context(
                patch.object(
                    generator,
                    '_generate',
                    return_value='ABCD12345678',
                )
            )
            exists = stack.enter_context(
                patch.object(
                    generator,
                    '_exists',
                    return_value=True,
                )
            )

            assert_that(
                calling(generator),
                raises(AttemptsIsOverError),
            )

            assert_that(generate.call_count, 3)
            assert_that(exists.call_count, 4)


class BookingTestCase(UserSetupMixin, MovieSessionSetupMixin, TestCase):
    def test_success_booking_on_minimals(self):
        self.movie_session_100_90.book_ticket(
            self.user_1,
            row_number=1,
            seat_number=1
        )

    def test_success_booking_on_highs(self):
        self.movie_session_100_90.book_ticket(
            self.user_1,
            row_number=self.movie_session_100_90.hall.rows_number,
            seat_number=self.movie_session_100_90.hall.seats_per_row,
        )

    def test_raises_on_unauthenticated_booking(self):
        assert_that(
            calling(self.movie_session_100_90.book_ticket).with_args(
                AnonymousUser(),
                row_number=1,
                seat_number=1,
            ),
            raises(ValidationError, 'Unauthenticated customer.')
        )

    def test_raises_on_booking_the_same_seat_twice(self):
        self.movie_session_100_90.book_ticket(self.user_1, 5, 5)

        assert_that(
            calling(self.movie_session_100_90.book_ticket).with_args(
                self.user_1,
                row_number=5,
                seat_number=5,
            ),
            raises(SeatNotAvailableError)
        )

    def test_raises_on_zero_row_number(self):
        assert_that(
            calling(self.movie_session_100_90.book_ticket).with_args(
                self.user_1,
                row_number=0,
                seat_number=1,
            ),
            raises(ValidationError, "Invalid row number.")
        )

    def test_raises_on_too_high_row_number(self):
        assert_that(
            calling(self.movie_session_100_90.book_ticket).with_args(
                self.user_1,
                row_number=self.movie_session_100_90.hall.rows_number + 1,
                seat_number=1,
            ),
            raises(ValidationError, "Invalid row number.")
        )

    def test_raises_on_zero_seat_number(self):
        assert_that(
            calling(self.movie_session_100_90.book_ticket).with_args(
                self.user_1,
                row_number=1,
                seat_number=0,
            ),
            raises(ValidationError, "Invalid seat number.")
        )

    def test_raises_on_too_high_seat_number(self):
        assert_that(
            calling(self.movie_session_100_90.book_ticket).with_args(
                self.user_1,
                row_number=1,
                seat_number=self.movie_session_100_90.hall.seats_per_row + 1,
            ),
            raises(ValidationError, "Invalid seat number.")
        )

    def test_raises_on_booking_too_late(self):
        assert_that(
            calling(self.movie_session_past.book_ticket).with_args(
                self.user_1,
                row_number=1,
                seat_number=1,
            ),
            raises(NoBookingAvailableError),
        )


class PaymentTestCase(TicketSetupMixin, TestCase):
    def test_success_payment(self):
        self.ticket_100_90.make_payment()

    def test_raises_on_second_payment(self):
        self.ticket_100_90.make_payment()

        assert_that(
            calling(self.ticket_100_90.make_payment),
            raises(TicketAlreadyPaidError),
        )

    def test_success_cancelation(self):
        self.ticket_100_90.cancel_booking()

    def test_raise_on_canceling_paid(self):
        self.ticket_100_90.make_payment()

        assert_that(
            calling(self.ticket_100_90.cancel_booking),
            raises(TicketAlreadyPaidError),
        )

    def test_raises_on_paying_too_late(self):
        ticket = Ticket.objects.create(
            movie_session=self.movie_session_past,
            customer=self.user_1,
            row_number=1,
            seat_number=1,
            cost=self.movie_session_past.ticket_cost,
        )
        assert_that(
            calling(ticket.make_payment),
            raises(NoBookingAvailableError),
        )
