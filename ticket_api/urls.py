"""ticket_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include
from django.urls import path
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django_registration.backends.one_step.views import RegistrationView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenVerifyView

from ticket_api.cinema.forms import RegistrationForm

urlpatterns = [
    path(
        r'',
        TemplateView.as_view(template_name='greeter.html'),
        name='greeter',
    ),
    path(r'api/', include('ticket_api.cinema.urls')),
    path(
        r'api/auth/token/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair',
    ),
    path(
        r'api/auth/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh',
    ),
    path(
        r'api/auth/token/verify/',
        TokenVerifyView.as_view(),
        name='token_verify',
    ),
    path(
        r'api/auth/',
        include('rest_framework.urls', namespace='rest_framework'),
    ),
    path(
        r'api/auth/register/',
        RegistrationView.as_view(
            form_class=RegistrationForm,
            success_url=reverse_lazy('api-root'),
        ),
        name='django_registration_register',
    ),
]
