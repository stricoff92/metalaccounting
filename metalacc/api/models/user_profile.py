

from django.db import models
from django.conf import settings

from api.utils import generate_slug


class UserProfile(models.Model):

    slug = models.SlugField(unique=True, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    use_nightmode = models.BooleanField(default=False)

    object_limit_companies = models.PositiveIntegerField(default=15)
    object_limit_periods_per_company = models.PositiveIntegerField(default=20)
    object_limit_entries_per_period = models.PositiveIntegerField(default=200)


    def __str__(self):
        return f"<UserProfile {self.pk} ({self.user})>"


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(UserProfile)
            if 'update_fields' in kwargs and 'slug' not in kwargs['update_fields']:
                kwargs['update_fields'] = list(chain(kwargs['update_fields'], ['slug']))
        
        return super().save(*args, **kwargs)
