# Generated by Django 3.0.8 on 2020-07-12 20:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0008_userprofile_object_limit_accounts'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='company',
            field=models.ForeignKey(blank=True, default=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.Company'),
        ),
        migrations.AddField(
            model_name='account',
            name='is_current',
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='account',
            unique_together={('user', 'company', 'number'), ('user', 'name')},
        ),
    ]
