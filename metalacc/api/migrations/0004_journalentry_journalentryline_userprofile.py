# Generated by Django 3.0.8 on 2020-07-11 20:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0003_account'),
    ]

    operations = [
        migrations.CreateModel(
            name='JournalEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(editable=False, unique=True)),
                ('date', models.DateField()),
                ('memo', models.CharField(blank=True, default=None, max_length=1000, null=True)),
                ('is_adjusting_entry', models.BooleanField(blank=True, default=False)),
                ('period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Period')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('use_nightmode', models.BooleanField(default=False)),
                ('object_limit_companies', models.PositiveIntegerField(default=15)),
                ('object_limit_periods_per_company', models.PositiveIntegerField(default=20)),
                ('object_limit_entries_per_period', models.PositiveIntegerField(default=200)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='JournalEntryLine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(editable=False, unique=True)),
                ('type', models.CharField(choices=[('c', 'Debit'), ('d', 'Credit')], max_length=1)),
                ('amount', models.PositiveIntegerField()),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Account')),
                ('journal_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='api.JournalEntry')),
            ],
        ),
    ]
