from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        PEMBUDIDAYA = "pembudidaya", "Pembudidaya"
        PAKAR = "pakar", "Pakar Perikanan"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PEMBUDIDAYA)
    no_telepon = models.CharField(max_length=20, blank=True)
    lokasi_kolam = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Pengguna"
        verbose_name_plural = "Pengguna"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_pakar(self):
        return self.role == self.Role.PAKAR
