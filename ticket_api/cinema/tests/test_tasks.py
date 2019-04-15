from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from hamcrest import assert_that
from hamcrest import calling
from hamcrest import raises

from ticket_api.cinema.models import Ticket
from ticket_api.cinema.tasks import cancel_non_paid_booking
from ticket_api.cinema.tests.mixins import TicketSetupMixin


class TaskTestCase(TicketSetupMixin, TestCase):
    def test_ticket_canceled(self):
        cancel_non_paid_booking(self.ticket_100_90.pk)

        assert_that(
            calling(Ticket.objects.get).with_args(pk=self.ticket_100_90.pk),
            raises(ObjectDoesNotExist)
        )
