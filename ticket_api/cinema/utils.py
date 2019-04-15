from django.utils import timezone


def local_time_as_naive():
    return timezone.localtime().replace(tzinfo=None)
