
import json

from api.models import Company, Account, Period, JournalEntry, JournalEntryLine

import jwt
from django.conf import settings
from django.core.signing import Signer
from django.db.models.functions import Cast
from django.db.models import CharField
from django.db import transaction
from django.utils import timezone

from api.utils import generate_slug, generate_slugs_batch


signer = Signer(key=settings.OBJECT_SIGNING_KEY)

# EXPORT FUNCTIONS # # # # # # # # # #

def export_company_to_jwt(company):
    data = {
        "meta":{
            'version':settings.OBJECT_SERIALIZATION_VERSION,
            'issued_at':timezone.now().strftime("%s"),
            'last_exported_by_author':company.user.id,
            'user_history':[
                {
                    'user_hash':company.user.userprofile.slug,
                    'timestamp':timezone.now().strftime("%s"),
                    'event':'export'
                }
            ] + company.user_finterprints
        }
    }

    # Serialize company.
    data['company'] = {"name":company.name}

    # Serialize periods
    data['periods'] = list(company.period_set
        .values("id")
        .annotate(
            start_str=Cast('start', CharField()),
            end_str=Cast('end', CharField())
        ))

    # Serialize accounts
    data['accounts'] = list(company.account_set.values(
        "id", "name", "number", "type", "tag", "is_contra", "is_current", "is_operating"))
    
    # serialize journal entries
    data['journal_entries'] = list(JournalEntry.objects
        .filter(period__company=company).values(
            "id", "period_id", "memo", "is_adjusting_entry", "is_closing_entry", "display_id")
        .annotate(date_str=Cast("date", CharField())))
    
    # Serialize journal entry lines
    data['journal_entry_lines'] = list(JournalEntryLine.objects
        .filter(journal_entry__period__company=company)
        .values(
            "journal_entry_id", "account_id", "type", "amount"))

    return jwt.encode(data, settings.OBJECT_SERIALIZATION_KEY, algorithm=settings.JWT_ALGORITHM).decode()


def sign_comapny_export_jwt(jwt:str):
    return signer.sign(jwt)



# IMPORT FUNCTIONS # # # # # # #

def decode_signed_jwt(signed_jwt:str):
    encoded_jwt = signer.unsign(signed_jwt)
    return jwt.decode(
        encoded_jwt,
        settings.OBJECT_SERIALIZATION_KEY,
        algorithms=[settings.JWT_ALGORITHM])



@transaction.atomic
def import_company_data(data:dict, user) -> Company:
    # TODO: use bulk_create

    # Create a new company
    company_name = data['company']['name']
    new_company_name = None
    if Company.objects.filter(user=user, name=company_name).exists():
        while True:
            slug_suffix = generate_slug(None)
            new_company_name = company_name[:Account.name.field.max_length - (len(slug_suffix) + 1)] + slug_suffix
            if not Company.objects.filter(user=user, name=new_company_name).exists():
                break
    else:
        new_company_name = company_name

    new_user_history = data['meta']['user_history'] + [{
        'user_hash':user.userprofile.slug,
        'timestamp':timezone.now().strftime("%s"),
        'event':'import',
    }]
    new_company = Company.objects.create(
        user=user, name=new_company_name,
        user_finger_print_str=json.dumps(new_user_history))


    data['company']['new_id'] = new_company.id

    # create new accounts
    account_map = {}
    for ix, account_data in enumerate(data['accounts']):
        new_account = Account.objects.create(
            company=new_company,
            user=user,
            name=account_data['name'],
            number=account_data['number'],
            type=account_data['type'],
            tag=account_data['tag'],
            is_contra=account_data['is_contra'],
            is_current=account_data['is_current'],
            is_operating=account_data['is_operating'])

        account_map[account_data['id']] = new_account


    # Create new periods
    period_map = {}
    for ix, period_data in enumerate(data['periods']):
        new_period = Period.objects.create(
            start=period_data['start_str'], end=period_data['end_str'], company=new_company)
        
        period_map[period_data['id']] = new_period
    

    # Create new Journal Entries
    journal_entry_map = {}
    for ix, journal_entry_data in enumerate(data['journal_entries']):
        new_journal_entry = JournalEntry.objects.create(
            period=period_map[journal_entry_data['period_id']],
            date=journal_entry_data['date_str'],
            memo=journal_entry_data['memo'],
            is_adjusting_entry=journal_entry_data['is_adjusting_entry'],
            is_closing_entry=journal_entry_data['is_closing_entry'],
        )
        journal_entry_map[journal_entry_data['id']] = new_journal_entry

    # Create journal entry lines
    new_journal_entry_lines = []
    jel_slugs = list(generate_slugs_batch(JournalEntryLine, len(data['journal_entry_lines'])))

    for ix, jel_data in enumerate(data['journal_entry_lines']):
        new_journal_entry_lines.append(JournalEntryLine(
            slug=jel_slugs[ix],
            journal_entry=journal_entry_map[jel_data['journal_entry_id']],
            account=account_map[jel_data['account_id']],
            type=jel_data['type'],
            amount=jel_data['amount'],
        ))
    JournalEntryLine.objects.bulk_create(new_journal_entry_lines)

    return new_company
