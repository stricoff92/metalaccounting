
from itertools import chain

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from api.utils import generate_slug


class JournalEntry(models.Model):

    slug = models.SlugField(unique=True, editable=False)
    period = models.ForeignKey("api.Period", on_delete=models.CASCADE)
    
    date = models.DateField()
    memo = models.CharField(max_length=1000, blank=True, null=True, default=None)
    is_adjusting_entry = models.BooleanField(blank=True, default=False)


    def __str__(self):
        return f"<JournalEntry {self.pk} {self.name} ({self.user})>"


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(JournalEntry)
            if 'update_fields' in kwargs and 'slug' not in kwargs['update_fields']:
                kwargs['update_fields'] = list(chain(kwargs['update_fields'], ['slug']))
        
        if not (self.period.start <= self.date <= self.period.end):
            raise ValidationError("entry date must fall within period")
        
        for je_line in self.lines.all():
            if je_line.account.user and je_line.account.user != self.period.user:
                raise ValidationError("period user does not equal account user")

        return super().save(*args, **kwargs)


class JournalEntryLine(models.Model):
    slug = models.SlugField(unique=True, editable=False)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey('api.Account', on_delete=models.CASCADE)

    TYPE_DEBIT = 'c'
    TYPE_CREDIT = 'd'
    TYPE_CHOICES = (
        (TYPE_DEBIT, 'Debit',),
        (TYPE_CREDIT, 'Credit',),
    )
    type = models.CharField(choices=TYPE_CHOICES, max_length=1)

    amount = models.PositiveIntegerField(blank=False, null=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(JournalEntryLine)
            if 'update_fields' in kwargs and 'slug' not in kwargs['update_fields']:
                kwargs['update_fields'] = list(chain(kwargs['update_fields'], ['slug']))
        
        if self.account.user and self.account.user != self.journal_entry.period.user:
            raise ValidationError("period user does not equal account user")


        return super().save(*args, **kwargs)
