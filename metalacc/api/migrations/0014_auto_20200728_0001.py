# Generated by Django 3.0.8 on 2020-07-28 00:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_auto_20200725_1637'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='account',
            unique_together={('company', 'number'), ('company', 'name')},
        ),
    ]