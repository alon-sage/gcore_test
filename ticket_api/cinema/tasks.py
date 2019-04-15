from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist


@shared_task
def cancel_non_paid_booking(ticket_pk):
    from ticket_api.cinema.models import Ticket

    try:
        ticket: Ticket = Ticket.objects.get(pk=ticket_pk)
    except ObjectDoesNotExist:
        return
    else:
        ticket.cancel_booking()
