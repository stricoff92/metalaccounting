

from django.db import models
from django.conf import settings

class UserProfile(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    use_nightmode = models.BooleanField(default=False)

    object_limit_companies = models.PositiveIntegerField(default=15)
    object_limit_periods_per_company = models.PositiveIntegerField(default=20)
    object_limit_entries_per_period = models.PositiveIntegerField(default=200)


    def __str__(self):
        return f"<UserProfile {self.pk} ({self.user})>"
