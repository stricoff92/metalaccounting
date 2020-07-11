
from itertools import chain

from django.db import models
from django.conf import settings

from api.utils import generate_slug


class Account(models.Model):

    slug = models.SlugField(unique=True, editable=False)
    name = models.CharField(max_length=100)
    user =  models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, default=None)
    

    TYPE_ASSET = 'asset'
    TYPE_LIABILITY = 'liability'
    TYPE_EQUITY = 'equity'
    TYPE_REVENUE = 'revenue'
    TYPE_EXPENSE = 'expense'
    TYPE_CHOICES = (
        (TYPE_ASSET, "Asset",),
        (TYPE_LIABILITY, "Liability",),
        (TYPE_EQUITY, "Equity",),
        (TYPE_REVENUE, "Revenue",),
        (TYPE_EXPENSE, "Expense",),
    )
    type = models.CharField(choices=TYPE_CHOICES, max_length=10)

    is_contra = models.BooleanField(default=False, blank=True, null=False)


    def __str__(self):
        return f"<Account {self.pk} {self.type}-{self.name} ({self.user})>"
    

    @property
    def is_default(self):
        return self.user is None


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(Account)
            if 'update_fields' in kwargs and 'slug' not in kwargs['update_fields']:
                kwargs['update_fields'] = list(chain(kwargs['update_fields'], ['slug']))
        
        return super().save(*args, **kwargs)
