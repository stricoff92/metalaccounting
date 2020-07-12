
from api.models import (
    Company,
    Period,
)

class TestObjectFactory:

    def create_company(self, user, name="foobar"):
        return Company.objects.create(user=user, name=name)

    def create_period(self, company, start, end):
        return Period.objects.create(company=company, start=start, end=end)
