
import json
from itertools import chain

from django.db import models
from django.conf import settings

from api.utils import generate_slug


class Company(models.Model):

    slug = models.SlugField(unique=True, editable=False)
    name = models.CharField(max_length=100)
    user =  models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_finger_print_str = models.TextField(blank=True, null=True, default=None)

    def __str__(self):
        return f"<Company {self.pk} {self.name} ({self.user})>"
    
    @property
    def user_finterprints(self):
        if self.user_finger_print_str:
            return json.loads(self.user_finger_print_str)
        else:
            return []

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(Company)
            if 'update_fields' in kwargs and 'slug' not in kwargs['update_fields']:
                kwargs['update_fields'] = list(chain(kwargs['update_fields'], ['slug']))
        
        return super().save(*args, **kwargs)
