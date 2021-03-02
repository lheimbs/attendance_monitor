from datetime import timedelta
import secrets
from uuid import uuid4

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
# from django.shortcuts import re
from django.utils.translation import ugettext_lazy as _
from macaddress.fields import MACAddressField
from django.urls import reverse


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

    # username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


# Create your models here.
class WeekDay(models.Model):
    MONDAY = 'MON'
    TUESDAY = 'TUE'
    WEDNESDAY = 'WED'
    THURSDAY = 'THU'
    FRIDAY = 'FRI'
    SATURDAY = 'SAT'
    SUNDAY = 'SUN'
    WEEKDAY_CHOICES = [
        (MONDAY, 'Monday'),
        (TUESDAY, 'Tuesday'),
        (WEDNESDAY, 'Wednesday'),
        (THURSDAY, 'Thursday'),
        (FRIDAY, 'Friday'),
        (SATURDAY, 'Saturday'),
        (SUNDAY, 'Sunday'),
    ]
    day = models.CharField(
        "course day",
        max_length=3,
        choices=WEEKDAY_CHOICES,
        default=MONDAY,
    )
    time = models.TimeField("starting time of course")

    def __str__(self):
        return "day: {}, time: {}".format(
            self.day, self.time
        )


def generate_token():
    return secrets.token_urlsafe(10)


class AccessToken(models.Model):
    token = models.CharField("Access Token", max_length=20, editable=False)
    created = models.DateTimeField("Time the token has been generated", editable=False)

    # added for future functionality where valid time is configurable
    valid_time = models.IntegerField("Minutes the token is valid for", default=90)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
            self.token = secrets.token_urlsafe(10)
        return super().save(*args, **kwargs)

    def is_token_valid(self, given_token):
        if self.token == given_token:
            return True
        return False

    def is_token_expired(self, custom_valid_time=None):
        expiration_time = self.created + timedelta(seconds=(custom_valid_time or self.valid_time)*60)
        if timezone.now() < expiration_time:
            return False
        return True

    def __str__(self):
        return f"created: {self.created}, valid for {self.valid_time}"


class Course(models.Model):
    name = models.CharField("course name", max_length=200)
    uuid = models.UUIDField("course identifier", primary_key=False, unique=True, default=uuid4, editable=False)
    min_attend_time = models.IntegerField("minimum time present to count as attended in minutes", default=45)
    duration = models.IntegerField("course duration in minutes", default=90)
    start_times = models.ManyToManyField(WeekDay)
    is_ongoing = models.BooleanField(default=False)

    access_token = models.OneToOneField(AccessToken, on_delete=models.CASCADE, null=True)

    def get_absolute_student_url(self):
        return reverse('student:detail', args=[str(self.id)])

    def get_absolute_student_leave_url(self):
        return reverse('student:leave_course', args=[str(self.id)])

    def get_absolute_student_register_url(self):
        if hasattr(self, 'access_token') and self.access_token:
            token = self.access_token.token
        else:
            token = ""
        return reverse('student:register_course', args=[str(self.id), token])

    def get_absolute_teacher_url(self):
        return reverse('teacher:detail', args=[str(self.id)])

    def get_absolute_teacher_delete_url(self):
        return reverse('teacher:delete', args=[str(self.id)])

    def get_absolute_teacher_edit_url(self):
        return reverse('teacher:edit', args=[str(self.id)])

    def __str__(self):
        return (
            f"name: {self.name}, "
            f"min_attend_time: {self.min_attend_time}, "
            f"duration: {self.duration}"
        )


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    student_nr = models.IntegerField("matrikel nr")
    mac = MACAddressField(null=True, blank=True, integer=False)
    courses = models.ManyToManyField(Course)

    def __str__(self):
        return f"user: {self.user}, stud.nr {self.student_nr}, mac: {self.mac}"


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    courses = models.ManyToManyField(Course)

    def __str__(self):
        return str(self.user)
