from django import template


register = template.Library()


@register.filter(name="get")
def filter_get(dictionary, key):
    return dictionary.get(key)
