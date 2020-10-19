

from django.conf import settings

def is_production():
    return settings.ENV == 'PROD'

def is_staging():
    return settings.ENV == 'STAGING'

def is_dev():
    return settings.ENV == 'DEV'


def grader_enabled():
    return not is_production()
