from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_422_UNPROCESSABLE_ENTITY


class AttemptsIsOverError(Exception):
    ...


class SeatNotAvailableError(Exception):
    ...


class TicketAlreadyPaidError(Exception):
    ...


class NoBookingAvailableError(Exception):
    ...


class MovieIsScheduledError(Exception):
    ...


class MovieSessionHasBookingsError(Exception):
    ...


class MovieSessionOverlapsError(Exception):
    ...


class SeatNotAvailableAPIError(APIException):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY
    default_code = 'seat_not_available'
    default_detail = 'Seat not available.'


class TicketAlreadyPaidAPIError(APIException):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY
    default_code = 'ticket_already_paid'
    default_detail = 'Ticket already paid.'


class NoBookingAvailableAPIError(APIException):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY
    default_code = 'no_booking_available'
    default_detail = 'No booking available.'


class MovieIsScheduledAPIError(APIException):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY
    default_code = 'movie_is_scheduled'
    default_detail = 'Movie is scheduled.'


class MovieSessionHasBookingsAPIError(APIException):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY
    default_code = 'movie_session_has_bookings'
    default_detail = 'Movie session has bookings.'


class MovieSessionOverlapsAPIError(APIException):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY
    default_code = 'movie_session_overlaps'
    default_detail = 'Movie session overlaps.'
