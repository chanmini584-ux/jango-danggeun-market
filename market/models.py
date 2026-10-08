from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    birth_date = models.DateField(verbose_name="생년월일")
    phone = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="휴대폰번호",
    )

    def __str__(self):
        return self.user.username
