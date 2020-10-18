
from django.db import models
from django.contrib.auth import get_user_model

class ContactUsSubmission(models.Model):
    user_email = models.CharField(blank=True, null=True, default=None, max_length=300)
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, blank=True, null=True, default=None)
    message = models.CharField(max_length=2050)
    created_at = models.DateTimeField()
