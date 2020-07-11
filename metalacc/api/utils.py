
import uuid

from django.conf import settings

def generate_slug(model):
    while True:
        slug = uuid.uuid4().hex[:settings.SLUG_LENGTH]
        if not model.objects.filter(slug=slug).exists():
            return slug
