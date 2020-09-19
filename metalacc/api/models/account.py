
from itertools import chain

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from api.utils import generate_slug, generate_slugs_batch


DEFAULT_ACCOUNTS = (
    # type    curr  contra operating number name tag
    ('asset', True, False, None, 1000, 'Cash', None,),
    ('asset', True, False, None, 1100, 'Office Supplies', None,),
    ('asset', True, False, None, 1500, 'A/R', None,),
    ('asset', True, False, None, 1700, 'Prepaid Expenses', None,),
    ('asset', True, False, None, 1600, 'Inventory', None,),
    ('asset', False, False, None, 1800, 'PPE', None,),
    ('asset', False, True, None, 1901, 'Accumulated Depreciation', None,),

    ('liability', True, False, None, 2100, 'A/P', None,),
    ('liability', True, False, None, 2200, 'Wages Payable', None,),
    ('liability', True, False, None, 2300, 'Insurance Payable', None,),
    ('liability', True, False, None, 2400, 'Interest Payable', None,),
    ('liability', True, False, None, 2500, 'Unearned Revenue', None,),
    ('liability', True, False, None, 2600, 'Dividends Payable', None,),
    ('liability', True, False, None, 2700, 'Rent Payable', None,),
    ('liability', True, False, None, 2800, 'Debt: Curr Term', None,),
    ('liability', False, False, None, 2900, 'Debt: Long Term', None,),

    ('equity', None, False, None, 3000, 'Common Stock', None,),
    ('equity', None, False, None, 3050, 'Prefered stock', None,),
    ('equity', None, False, None, 3400, 'APIC', None,),
    ('equity', None, False, None, 3700, 'Retained Earnings', None,),
    ('equity', None, True, None, 3901, 'Dividends', 'div',), # DIV TAG

    ('revenue', None, False, True, 4100, 'Sales Revenue', None,),
    ('revenue', None, False, True, 4200, 'Consulting Revenue', None,),
    ('revenue', None, False, False, 4300, 'Fee Revenue', None,),
    ('revenue', None, True, True, 4400, 'Discounts', None,),
    ('revenue', None, False, False, 4450, 'Gains', None,),

    ('expense', None, False, True, 5100, 'CoGS', 'cogs',), # COGS TAG
    ('expense', None, False, False, 5150, 'Depreciation Expenses', None,),
    ('expense', None, False, True, 5200, 'Wages Expenses', None,),
    ('expense', None, False, False, 5300, 'Tax Expenses', None,),
    ('expense', None, False, False, 5350, 'Interest Expenses', None,),
    ('expense', None, False, True, 5400, 'Insurance Expenses', None,),
    ('expense', None, False, False, 5500, 'Fee Expenses', None,),
    ('expense', None, False, False, 5600, 'Rent Expenses', None,),
    ('expense', None, False, False, 5700, 'Office Supplies Expenses', None,),
    ('expense', None, False,  False, 5800, 'Loses', None,),
)


class AccountManager(models.Manager):
    def create_default_accounts(self, company):
        accounts = []
        with transaction.atomic():
            slugs = list(generate_slugs_batch(self.model, len(DEFAULT_ACCOUNTS)))
            for ix, row in enumerate(DEFAULT_ACCOUNTS):
                accounts.append(self.model(
                    user=company.user, company=company, type=row[0], is_current=row[1],
                    is_contra=row[2], is_operating=row[3], number=row[4], name=row[5], tag=row[6], slug=slugs[ix]))
            accounts = self.model.objects.bulk_create(accounts)
        return accounts


class Account(models.Model):

    objects = AccountManager()
    
    user =  models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company =  models.ForeignKey('api.Company', on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, editable=False)

    TAG_DIVIDENDS = 'div'
    TAG_COST_OF_GOODS = 'cogs'
    ACCOUNT_TAGS_CHOICES = (
        (TAG_DIVIDENDS, "Dividends",),
        (TAG_COST_OF_GOODS, "Cost of Goods Sold",),
    )
    ACCOUNT_TAG_NAME_DICT = {r[0]:r[1] for r in ACCOUNT_TAGS_CHOICES}
    tag = models.CharField(
        choices=ACCOUNT_TAGS_CHOICES, max_length=5, blank=True, null=True, default=None)

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
    def human_readable_tag_name(self):
        return self.ACCOUNT_TAG_NAME_DICT.get(self.tag)


    @property
    def supports_is_current(self):
        return self.type in self.CURRENT_TYPES
    
    @property
    def supports_is_operating(self):
        return self.type in self.OPERATING_TYPES
    
    @property
    def available_tag_options(self):
        if self.type == self.TYPE_EXPENSE and not self.is_contra:
            return ((self.TAG_COST_OF_GOODS, "Cost of Goods Sold"),)
        elif self.type == self.TYPE_REVENUE and self.is_contra:
            return ((self.TAG_COST_OF_GOODS, "Cost of Goods Sold"),)
        elif self.type == self.TYPE_EQUITY and self.is_contra:
            return ((self.TAG_DIVIDENDS, "Dividends"),)
        else:
            return tuple()


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

        if self.tag == self.TAG_DIVIDENDS:
            if self.type != self.TYPE_EQUITY or not self.is_contra:
                raise ValidationError(f"Accounts with tag {self.ACCOUNT_TAG_NAME_DICT[self.tag]} must be a contra equity account.")

        if self.tag == self.TAG_COST_OF_GOODS:
            if not self.type in [self.TYPE_REVENUE, self.TYPE_EXPENSE]:
                raise ValidationError(f"Accounts with tag {self.ACCOUNT_TAG_NAME_DICT[self.tag]} must be an expense account.")
            if self.type == self.TYPE_REVENUE and not self.is_contra:
                raise ValidationError(f"Revenue account must be marked as a contra account to hold a Cost of Goods sold tag.")
            if self.type == self.TYPE_EXPENSE and self.is_contra:
                raise ValidationError(f"Expense accounts cannot be marked as a contra account to hold a Cost of Goods sold tag.")

        return super().save(*args, **kwargs)
