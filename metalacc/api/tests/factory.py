
from api.models import (
    Company
)

class TestObjectFactory:

    def create_company(self, user, name="foobar"):
        return Company.objects.create(user=user, name=name)
