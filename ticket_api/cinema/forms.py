from django_registration.forms import RegistrationForm as DjangoRegistrationForm

from ticket_api.cinema.models import User


class RegistrationForm(DjangoRegistrationForm):
    class Meta(DjangoRegistrationForm.Meta):
        model = User
        fields = [
            User.USERNAME_FIELD,
            'password1',
            'password2',
        ]
