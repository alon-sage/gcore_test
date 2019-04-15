from django.db.models import ProtectedError
from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.viewsets import ModelViewSet
from rest_framework.viewsets import ViewSet

from ticket_api.cinema.exceptions import MovieIsScheduledAPIError
from ticket_api.cinema.exceptions import MovieIsScheduledError
from ticket_api.cinema.exceptions import MovieSessionHasBookingsAPIError
from ticket_api.cinema.exceptions import MovieSessionHasBookingsError
from ticket_api.cinema.exceptions import MovieSessionOverlapsAPIError
from ticket_api.cinema.exceptions import MovieSessionOverlapsError
from ticket_api.cinema.exceptions import NoBookingAvailableAPIError
from ticket_api.cinema.exceptions import NoBookingAvailableError
from ticket_api.cinema.exceptions import SeatNotAvailableAPIError
from ticket_api.cinema.exceptions import SeatNotAvailableError
from ticket_api.cinema.exceptions import TicketAlreadyPaidAPIError
from ticket_api.cinema.exceptions import TicketAlreadyPaidError
from ticket_api.cinema.models import Hall
from ticket_api.cinema.models import Movie
from ticket_api.cinema.models import MovieSession
from ticket_api.cinema.models import Ticket
from ticket_api.cinema.models import User
from ticket_api.cinema.permissions import ReadOnly
from ticket_api.cinema.serializers import BookingForCustomerSerializer
from ticket_api.cinema.serializers import BookingSerializer
from ticket_api.cinema.serializers import HallAdminSerializer
from ticket_api.cinema.serializers import HallPublicSerializer
from ticket_api.cinema.serializers import MovieAdminSerializer
from ticket_api.cinema.serializers import MoviePublicSerializer
from ticket_api.cinema.serializers import MovieSessionAdminSerializer
from ticket_api.cinema.serializers import MovieSessionPublicSerializer
from ticket_api.cinema.serializers import SeatSchemaSerializer
from ticket_api.cinema.serializers import TicketAdminSerializer
from ticket_api.cinema.serializers import TicketPrivateSerializer
from ticket_api.cinema.serializers import UserAdminSerializer
from ticket_api.cinema.serializers import UserInfoSerializer


class UserInfoViewSet(ViewSet):
    def list(self, request):
        serializer = UserInfoSerializer(request.user)
        return Response(serializer.data)


class UserViewSet(ModelViewSet):
    permission_classes = (ReadOnly & IsAuthenticated & IsAdminUser,)
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    search_fields = ('^email', '$first_name', '$last_name')
    ordering = ('email',)


class HallViewSet(ModelViewSet):
    permission_classes = (ReadOnly,)
    queryset = Hall.objects.all()
    search_fields = ('$name',)
    ordering_fields = ('name',)
    ordering = ('name',)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return HallAdminSerializer
        else:
            return HallPublicSerializer


class MovieViewSet(ModelViewSet):
    permission_classes = (ReadOnly | (IsAuthenticated & IsAdminUser),)
    queryset = Movie.objects.all()
    filterset_fields = {
        'duration': ['gt', 'lt'],
    }
    search_fields = ('$name',)
    ordering_fields = ('name',)
    ordering = ('name',)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return MovieAdminSerializer
        else:
            return MoviePublicSerializer

    def perform_update(self, serializer):
        try:
            serializer.save()
        except (ProtectedError, MovieIsScheduledError):
            raise MovieIsScheduledAPIError()

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except (ProtectedError, MovieIsScheduledError):
            raise MovieIsScheduledAPIError()


class MovieSessionViewSet(ModelViewSet):
    permission_classes = (ReadOnly | (IsAuthenticated & IsAdminUser),)
    queryset = MovieSession.objects.all()
    filterset_fields = {
        'movie': ['exact'],
        'date': ['exact', 'gt', 'lt'],
        'starts_at': ['gt', 'lt'],
        'ticket_cost': ['gt', 'lt'],
    }
    ordering_fields = ('date', 'starts_at', 'ticket_cost')
    ordering = ('date', 'starts_at')

    def get_queryset(self):
        if self.request.user.is_staff:
            return MovieSession.objects.all()
        else:
            now = timezone.now()
            query = (
                    Q(date__gt=now.date()) |
                    (Q(date=now.date()) & Q(starts_at__gt=now.time()))
            )
            return MovieSession.objects.filter(query)

    def get_serializer_class(self):
        if self.action == 'book':
            return BookingSerializer
        elif self.action == 'book_for_customer':
            return BookingForCustomerSerializer
        elif self.request.user.is_staff:
            return MovieSessionAdminSerializer
        else:
            return MovieSessionPublicSerializer

    def perform_create(self, serializer):
        try:
            serializer.save()
        except MovieSessionOverlapsError:
            raise MovieSessionOverlapsAPIError()

    def perform_update(self, serializer):
        try:
            serializer.save()
        except MovieSessionOverlapsError:
            raise MovieSessionOverlapsAPIError()
        except (ProtectedError, MovieSessionHasBookingsError):
            raise MovieSessionHasBookingsAPIError()

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except (ProtectedError, MovieSessionHasBookingsError):
            raise MovieSessionHasBookingsAPIError()

    @detail_route(['GET'], permission_classes=(IsAuthenticated,))
    def seats(self, request, pk=None):
        movie_session: MovieSession = self.get_object()
        serializer = SeatSchemaSerializer(
            movie_session,
            context={'request': request},
        )
        return Response(serializer.data)

    @detail_route(['POST'], permission_classes=(IsAuthenticated,))
    def book(self, request, pk=None):
        movie_session: MovieSession = self.get_object()
        in_serializer = BookingSerializer(
            data=request.data,
            context={'movie_session': movie_session},
        )
        if in_serializer.is_valid():
            try:
                ticket = movie_session.book_ticket(
                    request.user,
                    row_number=in_serializer.validated_data['row_number'],
                    seat_number=in_serializer.validated_data['seat_number'],
                )
            except SeatNotAvailableError:
                raise SeatNotAvailableAPIError()
            except NoBookingAvailableError:
                raise NoBookingAvailableAPIError()

            if self.request.user.is_staff:
                serializer_class = TicketAdminSerializer
            else:
                serializer_class = TicketPrivateSerializer

            out_serializer = serializer_class(
                ticket,
                context={'request': request},
            )
            return Response(out_serializer.data)
        else:
            return Response(in_serializer.errors, HTTP_400_BAD_REQUEST)

    @detail_route(['POST'], permission_classes=(IsAuthenticated & IsAdminUser,))
    def book_for_customer(self, request, pk=None):
        movie_session: MovieSession = self.get_object()

        serializer = BookingForCustomerSerializer(
            data=request.data,
            context={'movie_session': movie_session},
        )
        if serializer.is_valid():
            validated_data = serializer.validated_data
            try:
                ticket = movie_session.book_ticket(
                    validated_data['customer'],
                    row_number=validated_data['row_number'],
                    seat_number=validated_data['seat_number'],
                )
            except SeatNotAvailableError:
                raise SeatNotAvailableAPIError()
            except NoBookingAvailableError:
                raise NoBookingAvailableAPIError()

            serializer = TicketAdminSerializer(
                ticket,
                context={'request': request},
            )
            return Response(serializer.data)
        else:
            return Response(serializer.errors, HTTP_400_BAD_REQUEST)


class TicketViewSet(ModelViewSet):
    permission_classes = (ReadOnly & IsAuthenticated,)
    queryset = Ticket.objects.all()

    def get_queryset(self):
        if self.request.user.is_staff:
            return Ticket.objects.all()
        else:
            return Ticket.objects.filter(customer=self.request.user)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return TicketAdminSerializer
        else:
            return TicketPrivateSerializer

    @detail_route(['POST'], permission_classes=(IsAuthenticated,))
    def pay(self, request, pk=None):
        ticket: Ticket = self.get_object()

        try:
            ticket.make_payment()
        except TicketAlreadyPaidError:
            raise TicketAlreadyPaidAPIError()
        except NoBookingAvailableError:
            raise NoBookingAvailableAPIError()

        serializer = self.get_serializer(ticket)
        return Response(serializer.data)

    @detail_route(['POST'], permission_classes=(IsAuthenticated & IsAdminUser,))
    def cancel(self, request, pk=None):
        ticket: Ticket = self.get_object()

        try:
            ticket.cancel_booking()
        except TicketAlreadyPaidError:
            raise TicketAlreadyPaidAPIError()

        return Response(status=HTTP_204_NO_CONTENT)
