from rest_framework.compat import MinValueValidator
from rest_framework.fields import BooleanField
from rest_framework.fields import IntegerField
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import Serializer

from ticket_api.cinema.models import Hall
from ticket_api.cinema.models import Movie
from ticket_api.cinema.models import MovieSession
from ticket_api.cinema.models import Ticket
from ticket_api.cinema.models import User
from ticket_api.cinema.validators import DynamicMaxValueValidator


class UserInfoSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'last_login', 'date_joined',
            'is_anonymous', 'is_authenticated',
        )


class AnonymousUserInfoSerializer(Serializer):
    is_anonymous = BooleanField()
    is_authenticated = BooleanField()


class UserAdminSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'last_login', 'date_joined')


class HallPublicSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Hall
        exclude = ('cleaning_duration',)

    capacity = IntegerField(read_only=True)


class HallAdminSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Hall
        fields = '__all__'

    capacity = IntegerField(read_only=True)


class MoviePublicSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Movie
        fields = '__all__'


class MovieAdminSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Movie
        fields = '__all__'


class MovieSessionPublicSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = MovieSession
        fields = (
            'url', 'hall', 'movie', 'date', 'starts_at', 'ticket_cost',
            'empty_seats',
        )

    empty_seats = IntegerField(read_only=True)


class MovieSessionAdminSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = MovieSession
        fields = '__all__'

    total_duration = IntegerField(read_only=True)
    booked_seats = IntegerField(read_only=True)
    empty_seats = IntegerField(read_only=True)


class InlineBookedSeats(ModelSerializer):
    class Meta:
        model = Ticket
        fields = ('row_number', 'seat_number')


class SeatSchemaSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = MovieSession
        fields = ('url', 'rows_number', 'seats_per_row', 'booked_seats')

    rows_number = IntegerField(source='hall.rows_number')
    seats_per_row = IntegerField(source='hall.seats_per_row')
    booked_seats = InlineBookedSeats(source='tickets', many=True)


class BookingSerializer(Serializer):
    row_number = IntegerField(
        validators=(
            MinValueValidator(1),
            DynamicMaxValueValidator(
                lambda context: context['movie_session'].hall.rows_number,
            ),
        )
    )
    seat_number = IntegerField(
        validators=(
            MinValueValidator(1),
            DynamicMaxValueValidator(
                lambda context: context['movie_session'].hall.seats_per_row,
            ),
        )
    )


class BookingForCustomerSerializer(BookingSerializer):
    customer = SlugRelatedField(
        slug_field='email',
        queryset=User.objects.all(),
    )


class InlineHallSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Hall
        fields = ('url', 'name')


class InlineMovieSessionSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = MovieSession
        fields = ('url', 'hall', 'movie', 'date', 'starts_at')

    hall = InlineHallSerializer()
    movie = MoviePublicSerializer()


class TicketPrivateSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Ticket
        fields = (
            'url', 'movie_session', 'row_number', 'seat_number', 'order_number',
            'cost', 'booked_at', 'paid_at',
        )

    movie_session = InlineMovieSessionSerializer()


class TicketAdminSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'

    customer = SlugRelatedField('email', queryset=User.objects.all())
