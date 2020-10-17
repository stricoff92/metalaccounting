
import os.path
import re
import uuid

from django.conf import settings
from django.db.models import Q, Max
from django.urls import reverse
from django.utils import timezone
import jwt

def some(args):
    return any(args) and not all(args)


def get_version_hash() -> str:
    return str(uuid.uuid4()).replace("-", "")


def generate_slug(model) -> str:
    if not model:
        return uuid.uuid4().hex[:settings.SLUG_LENGTH]

    while True:
        slug = uuid.uuid4().hex[:settings.SLUG_LENGTH]
        if not model.objects.filter(slug=slug).exists():
            return slug

def generate_slugs_batch(model, count:int) -> set:
    if count <= 0:
        return set()

    slugs = set(uuid.uuid4().hex[:settings.SLUG_LENGTH] for i in range(count))
    while len(slugs) < count:
        slugs.add(uuid.uuid4().hex[:settings.SLUG_LENGTH])
    
    while True:
        duplicate_slugs = model.objects.filter(slug__in=slugs).values_list("slug", flat=True)
        if not duplicate_slugs.exists():
            break
        slugs.difference_update(duplicate_slugs)
        while len(slugs) < count:
            slugs.add(uuid.uuid4().hex[:settings.SLUG_LENGTH])
    
    return slugs


VALID_SLUG_PATT = re.compile(r'^[a-zA-Z0-9]{10,}$')
def is_valid_slug(slug:str) -> bool:
    return bool(VALID_SLUG_PATT.match(slug))


def get_date_conflict_Q(start, end):
    return (
        Q(start__lte=start, end__gte=start)
        | Q(start__gte=start, start__lte=end)
        | Q(start__gte=start, end__lte=end)
        | Q(start__lte=start, end__gte=end))


def get_next_journal_entry_display_id_for_company(company) -> int:
    from api.models import JournalEntry
    last_id = JournalEntry.objects.filter(period__company=company).aggregate(m=Max("display_id"))['m'] or 0
    return last_id + 1


def get_report_page_breadcrumbs(period, report_name:str) -> list:
    company = period.company
    date_format = "%b %-d, %Y"
    return [
        {
            'value':company.name,
            'href':reverse("app-company", kwargs={'slug':company.slug}),
        }, {
            'value':'periods',
            'href':reverse("app-period", kwargs={'slug':company.slug})
        }, {
            'value':f'{period.start.strftime(date_format)} -> {period.end.strftime(date_format)}',
            'href':reverse("app-period-details", kwargs={'slug':period.slug})
        }, {
            'value':report_name,
        }
    ]


def get_company_periods_up_to_and_excluding(period):
    """ Get all periods for a company leading up to the given period, including the given period
    """
    company = period.company
    return (company.period_set
        .exclude(id=period.id)
        .filter(company=company, end__lte=period.start))

def get_company_periods_up_to(period):
    """ Get all periods for a company leading up to the given period, including the given period
    """
    company = period.company
    return (company.period_set
        .filter(company=company, end__lte=period.end))


def get_dr_cr_balance(dr_total:int, cr_total:int):
    balance = 0
    if dr_total > 0 and dr_total > cr_total:
        balance = dr_total - cr_total
    elif dr_total > 0 and dr_total < cr_total:
        balance =  cr_total - dr_total
    
    elif cr_total > 0 and cr_total > dr_total:
        balance =  cr_total - dr_total
    elif cr_total > 0 and cr_total < dr_total:
        balance = dr_total - cr_total
    
    return balance


def force_negative(val):
    return abs(val) * -1


def get_photo_gallery_images():
    return [
        'Apple2.jpg',
        'Excel.png',
        'Lotus123.jpg',
        'Pacioli.jpg',
        'Visicalc.jpg',
        'Abacus.jpg',
        "Ledger.jpg",
        'Calculator.png',
    ]


def get_account_activation_token(slug:str) -> str:
    claims = {
        'created_at':timezone.now().strftime("%s"),
        'slug':slug,
    }
    return jwt.encode(claims, settings.OBJECT_SERIALIZATION_KEY, algorithm=settings.JWT_ALGORITHM).decode()


def get_account_activation_url(slug:str, token:str) -> str:
    return os.path.join(settings.BASE_ABSOLUTE_URL, 'activate', slug) + "?token=" + token


def get_slug_from_account_activation_token(token:str) -> str:
    data = jwt.decode(
        token,
        settings.OBJECT_SERIALIZATION_KEY,
        algorithms=[settings.JWT_ALGORITHM])
    return data['slug']
