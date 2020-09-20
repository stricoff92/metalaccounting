
""" This model holds data required to build the statement of cash flows for a given period.
    This is needed because adjustments to cash accounts that impact other current assets
    could either be listed as an Operating activity or an investing activity.

    Revenue/Expenses   -> Operations Activity
    Non-Current Assets -> Investing Activity
    Liabilities/Equity -> Financing Activities

    Current Assets     ->  can be Operations Activity OR Investing Activity

"""


import json
from itertools import chain

from django.db import models
from django.conf import settings

from api.utils import generate_slug


class CashFlowWorksheet(models.Model):

    slug = models.SlugField(unique=True, editable=False)
    period = models.OneToOneField('api.Period', on_delete=models.CASCADE)
    version_hash = models.CharField(blank=False, null=False, max_length=40)

    data = models.TextField(blank=True, null=True, default=None)


    def __str__(self):
        return f"<Cashflow Worksheet {self.pk}>"
    

    @property
    def in_sync(self):
        return self.version_hash == self.period.version_hash
    

    @property
    def worksheet_data(self):
        if self.data:
            return json.loads(self.data)
        else:
            return {}


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(CashFlowWorksheet)
            if 'update_fields' in kwargs and 'slug' not in kwargs['update_fields']:
                kwargs['update_fields'] = list(chain(kwargs['update_fields'], ['slug']))
        
        return super().save(*args, **kwargs)
