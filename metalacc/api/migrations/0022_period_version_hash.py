# Generated by Django 3.0.8 on 2020-09-20 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_auto_20200920_1802'),
    ]

    operations = [
        migrations.AddField(
            model_name='period',
            name='version_hash',
            field=models.CharField(default='sdfasdfsadfasdf', max_length=40),
            preserve_default=False,
        ),
    ]
