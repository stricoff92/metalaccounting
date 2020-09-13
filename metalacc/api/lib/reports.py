
from collections import defaultdict

from django.db.models import Sum

from api.models import JournalEntry, JournalEntryLine, Account
from api.utils import (
    get_company_periods_up_to_and_excluding,
)

def get_trial_balance_data(current_period):
    company = current_period.company
    
    # Fetch all periods prior to this period
    past_periods = get_company_periods_up_to_and_excluding(current_period)

    # Fetch non-closing journal entries from this period
    current_unadjustedjournal_entries = JournalEntry.objects.filter_for_unadjusted_trial(
        current_period)
    current_adjusting_journal_entries = JournalEntry.objects.filter_for_adjusted_trial(
        current_period)

    current_unadjusted_jels = JournalEntryLine.objects.filter(
        journal_entry__in=current_unadjustedjournal_entries)
    current_adjusted_jels = JournalEntryLine.objects.filter(
        journal_entry__in=current_adjusting_journal_entries)

    # Aggregate DR/CR amounts by Account and is_adjusted
    get_default_row = lambda: {
        JournalEntryLine.TYPE_DEBIT:0,
        JournalEntryLine.TYPE_CREDIT:0,
    }
    unadjusted_amounts_by_account = defaultdict(get_default_row)
    adjusted_amounts_by_account = defaultdict(get_default_row)

    for jel_sums in (current_unadjusted_jels
            .values("account_id", "type")
            .annotate(amount=Sum("amount"))):

        account_id = jel_sums['account_id']
        jel_type = jel_sums['type']
        unadjusted_amounts_by_account[account_id][jel_type] += jel_sums['amount']

    for jel_sums in (current_adjusted_jels
            .values("account_id", "type")
            .annotate(amount=Sum("amount"))):

        account_id = jel_sums['account_id']
        jel_type = jel_sums['type']
        adjusted_amounts_by_account[account_id][jel_type] += jel_sums['amount']
    
    # prefretch account info
    accounts = (Account.objects
        .filter(company=company)
        .values("id", "slug", "type", "name", "number", "is_contra"))
    accounts = {a['id']:a for a in accounts}


    # Calculate Account Balances and Create report rows.
    all_acount_ids = set(
        list(unadjusted_amounts_by_account.keys()) 
        + list(adjusted_amounts_by_account.keys()))
    rows = []
    total_company_unadj_dr, total_company_unadj_cr = 0, 0
    total_company_adj_dr, total_company_adj_cr = 0, 0
    for account_id in all_acount_ids:
        unadjusted_dr_total = unadjusted_amounts_by_account[account_id][JournalEntryLine.TYPE_DEBIT]
        unadjusted_cr_total = unadjusted_amounts_by_account[account_id][JournalEntryLine.TYPE_CREDIT]
        adjusted_dr_total = adjusted_amounts_by_account[account_id][JournalEntryLine.TYPE_DEBIT]
        adjusted_cr_total = adjusted_amounts_by_account[account_id][JournalEntryLine.TYPE_CREDIT]

        if unadjusted_dr_total == unadjusted_cr_total and adjusted_dr_total == adjusted_cr_total:
            # Account is zeroed out
            continue
        
        # Get unadjusted balances
        unadj_dr_bal, unadj_cr_bal = 0, 0
        if unadjusted_dr_total > 0 and unadjusted_dr_total > unadjusted_cr_total: # DR accounts
            unadj_dr_bal = unadjusted_dr_total - unadjusted_cr_total
        elif unadjusted_dr_total > 0 and unadjusted_dr_total < unadjusted_cr_total:
            unadj_cr_bal = unadjusted_cr_total - unadjusted_dr_total

        elif unadjusted_cr_total > 0 and unadjusted_cr_total > unadjusted_dr_total: # CR accounts
            unadj_cr_bal = unadjusted_cr_total - unadjusted_dr_total
        elif unadjusted_cr_total > 0 and unadjusted_cr_total < unadjusted_dr_total:
            unadj_dr_bal = unadjusted_dr_total - unadjusted_cr_total
        
        # get adjusted balances
        adj_dr_bal, adj_cr_bal = 0, 0
        if adjusted_dr_total > 0 and adjusted_dr_total > adjusted_cr_total: # DR accounts
            adj_dr_bal = adjusted_dr_total - adjusted_cr_total
        elif unadjusted_dr_total > 0 and unadjusted_dr_total < unadjusted_cr_total:
            adj_cr_bal = adjusted_cr_total - adjusted_dr_total

        if adjusted_cr_total > 0 and adjusted_cr_total > adjusted_dr_total: # CR accounts
            adj_cr_bal = adjusted_cr_total - adjusted_dr_total
        elif adjusted_cr_total > 0 and adjusted_cr_total < adjusted_dr_total:
            adj_dr_bal = adjusted_dr_total - adjusted_cr_total


        if unadj_dr_bal or unadj_cr_bal or adj_dr_bal or adj_cr_bal:
            accounts[account_id]
            rows.append({
                'account':accounts[account_id],
                'unadj_dr_bal':unadj_dr_bal,
                'unadj_cr_bal':unadj_cr_bal,
                'adj_dr_bal':adj_dr_bal,
                'adj_cr_bal':adj_cr_bal,
            })

            total_company_unadj_dr += unadj_dr_bal
            total_company_unadj_cr += unadj_cr_bal
            total_company_adj_dr += adj_dr_bal
            total_company_adj_cr += adj_cr_bal
    
    rows.sort(key=lambda row: row['account']['number'])

    return (
        rows,
        total_company_unadj_dr,
        total_company_unadj_cr,
        total_company_adj_dr,
        total_company_adj_cr,
    )
