# Generated by Django 2.2 on 2019-04-15 16:42

import datetime
from decimal import Decimal

import django.core.validators
import django.utils.timezone
from django.conf import settings
from django.db import migrations
from django.db import models

import ticket_api.cinema.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('password',
                 models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True,
                                                    verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False,
                                                     help_text='Designates that this user has all permissions without explicitly assigning them.',
                                                     verbose_name='superuser status')),
                ('email',
                 models.EmailField(blank=True, max_length=254, unique=True,
                                   verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False,
                                                 help_text='Designates whether the user can log into this admin site.',
                                                 verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True,
                                                  help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
                                                  verbose_name='active')),
                ('date_joined',
                 models.DateTimeField(default=django.utils.timezone.now,
                                      verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True,
                                                  help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
                                                  related_name='user_set',
                                                  related_query_name='user',
                                                  to='auth.Group',
                                                  verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True,
                                                            help_text='Specific permissions for this user.',
                                                            related_name='user_set',
                                                            related_query_name='user',
                                                            to='auth.Permission',
                                                            verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
        ),
        migrations.CreateModel(
            name='Hall',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True,
                                          validators=[
                                              django.core.validators.MinLengthValidator(
                                                  1)])),
                ('rows_number', models.IntegerField(
                    validators=[django.core.validators.MinValueValidator(1)])),
                ('seats_per_row', models.IntegerField(
                    validators=[django.core.validators.MinValueValidator(1)])),
                ('cleaning_duration', models.IntegerField(default=15,
                                                          validators=[
                                                              django.core.validators.MinValueValidator(
                                                                  1)])),
            ],
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True,
                                          validators=[
                                              django.core.validators.MinLengthValidator(
                                                  1)])),
                ('duration', models.IntegerField(
                    validators=[django.core.validators.MinValueValidator(1)])),
            ],
        ),
        migrations.CreateModel(
            name='MovieSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('starts_at', models.TimeField(validators=[
                    django.core.validators.MinValueValidator(
                        datetime.time(8, 0)),
                    django.core.validators.MaxValueValidator(
                        datetime.time(23, 0))])),
                ('ticket_cost',
                 models.DecimalField(decimal_places=2, max_digits=14,
                                     validators=[
                                         django.core.validators.MinValueValidator(
                                             Decimal('0'))])),
                ('advertise_duration', models.IntegerField(default=10,
                                                           validators=[
                                                               django.core.validators.MinValueValidator(
                                                                   0)])),
                ('hall',
                 models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                   related_name='movie_sessions',
                                   to='cinema.Hall')),
                ('movie',
                 models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                   related_name='movie_sessions',
                                   to='cinema.Movie')),
            ],
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('row_number', models.IntegerField(
                    validators=[django.core.validators.MinValueValidator(1)])),
                ('seat_number', models.IntegerField(
                    validators=[django.core.validators.MinValueValidator(1)])),
                ('order_number', models.CharField(
                    default=ticket_api.cinema.models.OrderNumberGenerator(4, 8),
                    max_length=12, unique=True, validators=[
                        django.core.validators.MinLengthValidator(12)])),
                ('cost', models.DecimalField(decimal_places=2, max_digits=14,
                                             validators=[
                                                 django.core.validators.MinValueValidator(
                                                     Decimal('0'))])),
                ('booked_at',
                 models.DateTimeField(default=django.utils.timezone.now)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('customer',
                 models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                   related_name='tickets',
                                   to=settings.AUTH_USER_MODEL)),
                ('movie_session',
                 models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                   related_name='tickets',
                                   to='cinema.MovieSession')),
            ],
            options={
                'unique_together': {
                    ('movie_session', 'row_number', 'seat_number')},
            },
        ),
    ]