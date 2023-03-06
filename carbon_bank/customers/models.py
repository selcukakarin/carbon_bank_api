import uuid

from django.contrib.auth.models import User
from django.db import models

from cores.models import CustomBaseClass


class Customer(CustomBaseClass):
    MALE = 'male'
    FEMALE = 'female'
    SEX_CHOICES = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
    )

    guid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    identity_number = models.CharField(max_length=60, unique=True)
    address = models.TextField()
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    sex = models.CharField(choices=SEX_CHOICES, max_length=6)

    def __str__(self):
        return f" Username: {self.user.username}, FirstName: {self.user.first_name}, LastName: {self.user.last_name}"

    @property
    def fullname(self):
        return f"{self.user.first_name} {self.user.last_name}"
