# Generated by Django 3.0.8 on 2020-09-20 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0020_auto_20200920_1626'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='tag',
            field=models.CharField(blank=True, choices=[('re', 'Retained Earnings'), ('cogs', 'Cost of Goods Sold')], default=None, max_length=5, null=True),
        ),
    ]
