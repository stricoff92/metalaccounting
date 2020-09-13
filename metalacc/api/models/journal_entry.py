
from itertools import chain

from django.db import models
from django.db.models import Sum, Q
from django.conf import settings
from django.core.exceptions import ValidationError

from api.utils import (
    generate_slug,
    get_next_journal_entry_display_id_for_company,
)


JOURNAL_ENTRY_TYPE_DR = 'd'
JOURNAL_ENTRY_TYPE_CR = 'c'


class JounralEntryManager(models.Manager):
    def filter_for_unadjusted_trial(self, period):
        """ Get all current regular entries, and all entries from pervious periods.
        """
        return self.filter(
            Q(period=period, is_adjusting_entry=False, is_closing_entry=False)
            | (
                ~Q(period=period)
                & Q(period__company=period.company)
                & Q(period__end__lte=period.start)
            )
        )

    def filter_for_adjusted_trial(self, period):
        """ Get all current regular & adjusting entries, and all entries from pervious periods.
        """
        return self.filter(
            Q(period=period, is_closing_entry=False)
            | (
                ~Q(period=period)
                & Q(period__company=period.company)
                & Q(period__end__lte=period.start)
            )
        )



class JournalEntry(models.Model):

    objects = JounralEntryManager()


    slug = models.SlugField(unique=True, editable=False)
    period = models.ForeignKey("api.Period", on_delete=models.CASCADE)
    
    date = models.DateField()
    memo = models.CharField(max_length=1000, blank=True, null=True, default=None)
    is_adjusting_entry = models.BooleanField(blank=True, default=False)
    is_closing_entry = models.BooleanField(blank=True, default=False)

    display_id = models.PositiveIntegerField()


    def __str__(self):
        return f"<JournalEntry {self.pk} ({self.period.user})>"

    @property
    def dr_total(self):
        value = self.lines.filter(type=JOURNAL_ENTRY_TYPE_DR).aggregate(s=Sum('amount'))['s']
        return value or 0

    @property
    def cr_total(self):
        value = self.lines.filter(type=JOURNAL_ENTRY_TYPE_CR).aggregate(s=Sum('amount'))['s']
        return value or 0

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(JournalEntry)
            if 'update_fields' in kwargs and 'slug' not in kwargs['update_fields']:
                kwargs['update_fields'] = list(chain(kwargs['update_fields'], ['slug']))
        
        if not self.display_id:
            self.display_id = get_next_journal_entry_display_id_for_company(self.period.company)
            if 'update_fields' in kwargs and 'display_id' not in kwargs['update_fields']:
                kwargs['update_fields'] = list(chain(kwargs['update_fields'], ['display_id']))

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

    TYPE_DEBIT = JOURNAL_ENTRY_TYPE_DR
    TYPE_CREDIT = JOURNAL_ENTRY_TYPE_CR
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
