import random
import string
from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import MaxValueValidator
from django.core.validators import MinLengthValidator
from django.core.validators import MinValueValidator
from django.db import IntegrityError
from django.db import transaction
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateField
from django.db.models import DateTimeField
from django.db.models import DecimalField
from django.db.models import EmailField
from django.db.models import ForeignKey
from django.db.models import IntegerField
from django.db.models import Model
from django.db.models import PROTECT
from django.db.models import TimeField
from django.db.models.signals import pre_delete
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext as _

from ticket_api.cinema.exceptions import AttemptsIsOverError
from ticket_api.cinema.exceptions import MovieIsScheduledError
from ticket_api.cinema.exceptions import MovieSessionHasBookingsError
from ticket_api.cinema.exceptions import MovieSessionOverlapsError
from ticket_api.cinema.exceptions import NoBookingAvailableError
from ticket_api.cinema.exceptions import SeatNotAvailableError
from ticket_api.cinema.exceptions import TicketAlreadyPaidError
from ticket_api.cinema.managers import UserManager
from ticket_api.cinema.tasks import cancel_non_paid_booking
from ticket_api.cinema.utils import local_time_as_naive
from ticket_api.cinema.validators import NonNegativeDecimal
from ticket_api.cinema.validators import NonNegativeInt
from ticket_api.cinema.validators import NotBlank
from ticket_api.cinema.validators import PositiveInt


class User(AbstractBaseUser, PermissionsMixin):
    email = EmailField(_('email address'), unique=True, blank=True)
    is_staff = BooleanField(
        _('staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),
    )
    is_active = BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return self.email


class Hall(Model):
    name = CharField(max_length=256, unique=True, validators=[NotBlank])
    rows_number = IntegerField(validators=[PositiveInt])
    seats_per_row = IntegerField(validators=[PositiveInt])
    cleaning_duration = IntegerField(default=15, validators=[PositiveInt])

    @property
    def capacity(self):
        return self.rows_number * self.seats_per_row

    def __str__(self):
        return self.name


class Movie(Model):
    name = CharField(max_length=256, unique=True, validators=[NotBlank])
    duration = IntegerField(validators=[PositiveInt])

    def __str__(self):
        return self.name


@receiver([pre_save, pre_delete], sender=Movie)
def check_movie_not_scheduled(sender, instance, **kwargs):
    if instance.movie_sessions.exists():
        raise MovieIsScheduledError()


class MovieSession(Model):
    movie = ForeignKey(Movie, on_delete=PROTECT, related_name='movie_sessions')
    hall = ForeignKey(Hall, on_delete=PROTECT, related_name='movie_sessions')
    date = DateField()
    starts_at = TimeField(
        validators=[
            MinValueValidator(settings.MOVIE_SESSION_EARLIEST_OPEN_TIME),
            MaxValueValidator(settings.MOVIE_SESSION_LATEST_OPEN_TIME),
        ],
    )
    ticket_cost = DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[NonNegativeDecimal],
    )
    advertise_duration = IntegerField(default=10, validators=[NonNegativeInt])

    @property
    def total_duration(self) -> int:
        return (
                self.advertise_duration +
                self.movie.duration +
                self.hall.cleaning_duration
        )

    @property
    def booked_seats(self) -> int:
        return self.tickets.count()

    @property
    def empty_seats(self) -> int:
        return self.hall.capacity - self.booked_seats

    @property
    def is_booking_closed(self):
        time_remains: timedelta = (
                datetime.combine(self.date, self.starts_at) -
                local_time_as_naive()

        )
        return time_remains <= settings.BOOKING_CLOSE_PERIOD

    def save(self, *args, **kwargs):
        self.full_clean()
        super(MovieSession, self).save(*args, **kwargs)

    def clean(self):
        super(MovieSession, self).clean()

        starts_at = datetime.combine(self.date, self.starts_at)
        ends_at = (starts_at + timedelta(minutes=self.total_duration))

        qs = MovieSession.objects.filter(
            hall=self.hall,
            date__range=(starts_at.date(), ends_at.date()),
        )

        for movie_session in qs:
            if self != movie_session and self.has_overlap(movie_session):
                raise MovieSessionOverlapsError()

    def has_overlap(self, other: 'MovieSession') -> bool:
        start = datetime.combine(self.date, self.starts_at)
        end = start + timedelta(minutes=self.total_duration)

        other_start = datetime.combine(other.date, other.starts_at)
        other_end = other_start + timedelta(minutes=other.total_duration)

        overlap = min(end, other_end) - max(start, other_start)

        return overlap > timedelta()

    @transaction.atomic
    def book_ticket(
            self,
            customer: User,
            row_number: int,
            seat_number: int,
    ) -> 'Ticket':
        # Before booking ticket check that movie session is valid
        self.full_clean()

        errors = {}

        # We are expecting authenticated and valid user
        if customer.is_authenticated:
            try:
                customer.full_clean()
            except ValidationError as e:
                errors['customer'] = e
        else:
            errors['customer'] = ValidationError(
                'Unauthenticated customer.',
                'unauthenticated_customer',
            )

        if row_number < 1 or row_number > self.hall.rows_number:
            errors['row_number'] = ValidationError(
                'Invalid row number.',
                'invalid_row_number',
            )

        if seat_number < 1 or seat_number > self.hall.seats_per_row:
            errors['row_number'] = ValidationError(
                'Invalid seat number.',
                'invalid_seat_number',
            )

        if errors:
            raise ValidationError(errors)

        if self.is_booking_closed:
            raise NoBookingAvailableError()

        try:
            ticket = Ticket.objects.create(
                movie_session=self,
                customer=customer,
                row_number=row_number,
                seat_number=seat_number,
                cost=self.ticket_cost,
            )
        except IntegrityError:
            raise SeatNotAvailableError()
        else:
            start_dt = datetime.combine(
                self.date,
                self.starts_at,
            ).astimezone(timezone.get_default_timezone())
            auto_cancelation_dt = start_dt - settings.BOOKING_CLOSE_PERIOD

            transaction.on_commit(
                lambda: cancel_non_paid_booking.apply_async(
                    (ticket.pk,),
                    eta=auto_cancelation_dt,
                ),
            )

            return ticket

    def __str__(self):
        return f'{self.movie} at {self.date} in "{self.hall}"'


@receiver([pre_save, pre_delete], sender=MovieSession)
def check_movie_session_has_no_bookings(sender, instance, **kwargs):
    if instance.tickets.exists():
        raise MovieSessionHasBookingsError()


@deconstructible
class OrderNumberGenerator:
    def __init__(self, serial_length, number_length, max_retries=3):
        self.serial_length = serial_length
        self.number_length = number_length
        self.max_retries = max_retries

    def _generate(self):
        serial = random.choices(string.ascii_uppercase, k=self.serial_length)
        number = random.choices(string.digits, k=self.number_length)
        return ''.join(serial + number)

    def _exists(self, value):
        return Ticket.objects.filter(order_number=value).exists()

    def __call__(self):
        value = self._generate()
        try_number = 1
        while self._exists(value):
            if try_number >= self.max_retries:
                raise AttemptsIsOverError()

            value = self._generate()
            try_number += 1
        return value


class Ticket(Model):
    class Meta:
        unique_together = ('movie_session', 'row_number', 'seat_number')

    movie_session = ForeignKey(
        MovieSession,
        on_delete=PROTECT,
        related_name='tickets',
    )
    customer = ForeignKey(
        User,
        on_delete=PROTECT,
        related_name='tickets',
    )
    row_number = IntegerField(validators=[PositiveInt])
    seat_number = IntegerField(validators=[PositiveInt])
    order_number = CharField(
        max_length=12,
        unique=True,
        default=OrderNumberGenerator(4, 8),
        validators=[MinLengthValidator(12)]
    )
    cost = DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[NonNegativeDecimal],
    )
    booked_at = DateTimeField(default=timezone.now)
    paid_at = DateTimeField(null=True, blank=True)

    @transaction.atomic
    def make_payment(self):
        self.full_clean()

        if self.paid_at is not None:
            raise TicketAlreadyPaidError('Ticket already paid.')

        if self.movie_session.is_booking_closed:
            raise NoBookingAvailableError()

        self.paid_at = timezone.now()
        self.save()

    @transaction.atomic
    def cancel_booking(self):
        if self.paid_at is not None:
            raise TicketAlreadyPaidError('Ticket already paid.')

        self.delete()

    def __str__(self):
        return (
            f'{self.movie_session} '
            f'(row {self.row_number}, seat {self.seat_number})'
        )
