
from itertools import chain

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from api.utils import generate_slug, generate_slugs_batch


DEFAULT_ACCOUNTS = (
    # type    curr  contra operating number name  
    ('asset', True, False, None, 1000, 'Cash',),
    ('asset', True, False, None, 1100, 'Office Supplies',),
    ('asset', True, False, None, 1500, 'A/R', '1500',),
    ('asset', True, False, None, 1700, 'Prepaid Expenses',),
    ('asset', True, False, None, 1600, 'Inventory',),
    ('asset', False, False, None, 1800, 'PPE',),
    ('asset', False, True, None, 1901, 'Accumulated Depreciation',),

    ('liability', True, False, None, 2100, 'A/P',),
    ('liability', True, False, None, 2200, 'Wages Payable',),
    ('liability', True, False, None, 2300, 'Insurance Payable',),
    ('liability', True, False, None, 2400, 'Interest Payable',),
    ('liability', True, False, None, 2500, 'Unearned Revenue',),
    ('liability', True, False, None, 2600, 'Dividends Payable',),
    ('liability', True, False, None, 2700, 'Rent Payable',),
    ('liability', True, False, None, 2800, 'Debt: Curr Term',),
    ('liability', False, False, None, 2900, 'Debt: Long Term',),

    ('equity', None, False, None, 3000, 'Common Stock',),
    ('equity', None, False, None, 3050, 'Prefered stock',),
    ('equity', None, False, None, 3400, 'APIC',),
    ('equity', None, False, None, 3700, 'Retained Earnings',),
    ('equity', None, True, None, 3901, 'Dividends',),

    ('revenue', None, False, True, 4100, 'Sales Revenue',),
    ('revenue', None, False, True, 4200, 'Consulting Revenue',),
    ('revenue', None, False, False, 4300, 'Fee Revenue',),
    ('revenue', None, True, True, 4400, 'Discounts',),
    ('revenue', None, False, False, 4450, 'Gains',),

    ('expense', None, False, True, 5100, 'CoGS',),
    ('expense', None, False, False, 5150, 'Depreciation Expenses',),
    ('expense', None, False, True, 5200, 'Wages Expenses',),
    ('expense', None, False, False, 5300, 'Tax Expenses',),
    ('expense', None, False, False, 5350, 'Interest Expenses',),
    ('expense', None, False, True, 5400, 'Insurance Expenses',),
    ('expense', None, False, False, 5500, 'Fee Expenses',),
    ('expense', None, False, False, 5600, 'Rent Expenses',),
    ('expense', None, False, False, 5700, 'Office Supplies Expenses',),
    ('expense', None, False,  False, 5800, 'Loses',),
)


class AccountManager(models.Manager):
    def create_default_accounts(self, company):
        accounts = []
        with transaction.atomic():
            slugs = list(generate_slugs_batch(Account, len(DEFAULT_ACCOUNTS)))
            for ix, row in enumerate(DEFAULT_ACCOUNTS):
                accounts.append(Account(
                    user=company.user, company=company, type=row[0], is_current=row[1],
                    is_contra=row[2], is_operating=row[3], number=row[4], name=row[5], slug=slugs[ix]))
            accounts = Account.objects.bulk_create(accounts)
        return accounts


class Account(models.Model):

    objects = AccountManager()
    
    user =  models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company =  models.ForeignKey('api.Company', on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, editable=False)

    TYPE_ASSET = 'asset'
    TYPE_LIABILITY = 'liability'
    TYPE_EQUITY = 'equity'
    TYPE_REVENUE = 'revenue'
    TYPE_EXPENSE = 'expense'
    CURRENT_TYPES = (TYPE_ASSET, TYPE_LIABILITY,)
    BALANCE_SHEET_TYPES = (TYPE_ASSET, TYPE_LIABILITY, TYPE_EQUITY,)
    OPERATING_TYPES = (TYPE_REVENUE, TYPE_EXPENSE,)
    TYPE_CHOICES = (
        (TYPE_ASSET, "Asset",),
        (TYPE_LIABILITY, "Liability",),
        (TYPE_EQUITY, "Equity",),
        (TYPE_REVENUE, "Revenue",),
        (TYPE_EXPENSE, "Expense",),
    )
    type = models.CharField(choices=TYPE_CHOICES, max_length=10)


    is_contra = models.BooleanField(default=False, blank=True, null=False)
    is_current = models.BooleanField(blank=True, null=True, default=None)
    is_operating = models.BooleanField(blank=True, null=True, default=None)
    number = models.PositiveIntegerField(blank=False, null=False)

    
    class Meta:
        unique_together = (
            ('company', 'name',),
            ('company', 'number',),
        )


    def __str__(self):
        return f"<Account {self.pk} {self.type}-{self.name} ({self.user})>"


    @property
    def supports_is_current(self):
        return self.type in self.CURRENT_TYPES
    
    @property
    def supports_is_operating(self):
        return self.type in self.OPERATING_TYPES


    @property
    def balance_type(self):
        if self.type in (self.TYPE_ASSET, self.TYPE_EXPENSE,):
            if self.is_contra:
                return "credit"
            else:
                return "debit"
        else:
            if self.is_contra:
                return "debit"
            else:
                return "credit"
    
    @property
    def is_dr(self):
        return self.balance_type == 'debit'

    @property
    def is_cr(self):
        return self.balance_type == 'credit'


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(Account)
            if 'update_fields' in kwargs and 'slug' not in kwargs['update_fields']:
                kwargs['update_fields'] = list(chain(kwargs['update_fields'], ['slug']))
        
        if self.company and self.company.user != self.user:
            raise ValidationError("company user mismatch")
        
        if self.is_current is not None and self.type not in self.CURRENT_TYPES:
            raise ValidationError("is_current cannot be assigned to this accoount type")
        
        if self.type in self.CURRENT_TYPES and self.is_current is None:
            raise ValidationError("is_current cannot be None for this accoount type")
        
        if self.type in self.OPERATING_TYPES and self.is_operating is None:
            raise ValidationError("is_operating cannot be None for this accoount type")
        
        if not self.type in self.OPERATING_TYPES and not self.is_operating is None:
            raise ValidationError("is_operating must be None for this accoount type")

        return super().save(*args, **kwargs)
