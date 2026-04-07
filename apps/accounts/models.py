
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from drf_commons.models import BaseModelMixin, TimeStampMixin

class GuestUser(TimeStampMixin, models.Model):
    """
    Model representing a guest user with limited access.
    """
    id = models.UUIDField(
        default=uuid.uuid4,
        primary_key=True,
        editable=False,
        help_text="Unique identifier for this guest user.",
    )

    def __str__(self):
        return str(self.id).capitalize()
    
class User(BaseModelMixin, AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    """

    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"