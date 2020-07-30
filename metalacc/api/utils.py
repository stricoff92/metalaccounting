
import re
import uuid

from django.conf import settings
from django.db.models import Q

def generate_slug(model):
    while True:
        slug = uuid.uuid4().hex[:settings.SLUG_LENGTH]
        if not model.objects.filter(slug=slug).exists():
            return slug

def generate_slugs_batch(model, count:int):
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
