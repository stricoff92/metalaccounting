
from itertools import chain

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ValidationError

from api.utils import generate_slug, get_date_conflict_Q


class Period(models.Model):

    slug = models.SlugField(unique=True, editable=False)
    company = models.ForeignKey('api.Company', on_delete=models.CASCADE)

    start = models.DateField(blank=False, null=False)
    end = models.DateField(blank=False, null=False)


    def __str__(self):
        return f"<Period {self.pk} {self.start} -> {self.end} ({self.user})>"


    @property
    def user(self):
        return self.company.user
    
    @property
    def days_count(self):
        delta = self.end - self.start
        return delta.days + 1
    
    @property
    def period_before(self):
        return self.company.period_set.exclude(id=self.id).filter(start__lt=self.start).order_by('-start').first()


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(Period)
            if 'update_fields' in kwargs and 'slug' not in kwargs['update_fields']:
                kwargs['update_fields'] = list(chain(kwargs['update_fields'], ['slug']))
        
        if self.start >= self.end:
            raise ValidationError("start cannot be after end")
        
        Q_date_conflict = get_date_conflict_Q(self.start, self.end)
        conflicting_periods = Period.objects.filter(
            Q(company=self.company)
            & Q_date_conflict)
        if self.pk:
            conflicting_periods = conflicting_periods.exclude(pk=self.pk)
        if conflicting_periods.exists():
            raise ValidationError(
                f"start and end date overlaps with another period: {conflicting_periods.values_list('pk', flat=True)}")
    
        return super().save(*args, **kwargs)
