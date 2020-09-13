
import re
import uuid

from django.conf import settings
from django.db.models import Q, Max
from django.urls import reverse

def generate_slug(model) -> str:
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
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'companies',
            'href':reverse("app-landing"),
        }, {
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
