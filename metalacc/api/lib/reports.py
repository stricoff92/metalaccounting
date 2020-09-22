
from collections import defaultdict, Counter

from django.db.models import Q, Sum

from api.models import JournalEntry, JournalEntryLine, Account
from api.utils import (
    get_company_periods_up_to_and_excluding,
    get_company_periods_up_to,
    get_dr_cr_balance,
    force_negative,
    some,
)

def get_trial_balance_data(current_period):
    company = current_period.company

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


def get_t_account_data_for_account(account, current_period) -> tuple:
    if account.company != current_period.company:
        raise ValueError("account and period must belong to the same company")

    all_periods = get_company_periods_up_to(current_period)
    previous_periods = get_company_periods_up_to_and_excluding(current_period)
    previous_period_ids = set(previous_periods.values_list("id", flat=True))

    all_jels = JournalEntryLine.objects.filter(
        journal_entry__period__in=all_periods,
        account=account)
    
    prev_dr_total = 0
    curr_dr_total = 0
    prev_cr_total = 0
    curr_cr_total = 0
    rows = []

    for jel in all_jels.order_by("journal_entry__date").values(
        "type", "amount", "slug",
        "journal_entry__period_id",
        "journal_entry__slug",
        "journal_entry__is_adjusting_entry",
        "journal_entry__is_closing_entry",
        "journal_entry__display_id",
        "journal_entry__date"):

        if jel['journal_entry__period_id'] in previous_period_ids:
            if jel['type'] == JournalEntryLine.TYPE_DEBIT:
                prev_dr_total += jel['amount']
            else:
                prev_cr_total += jel['amount']

        if jel['type'] == JournalEntryLine.TYPE_DEBIT:
            curr_dr_total += jel['amount']
        else:
            curr_cr_total += jel['amount']
        
        if jel['journal_entry__period_id'] == current_period.id:
            rows.append(jel)


    start_balance = get_dr_cr_balance(prev_dr_total, prev_cr_total)
    end_balance = get_dr_cr_balance(curr_dr_total, curr_cr_total)

    return (
        rows,
        start_balance,
        end_balance,
        prev_dr_total,
        prev_cr_total,
        curr_dr_total,
        curr_cr_total,
    )


KEY_OPERATING_REVENUE = 'operating_revenue'
KEY_NON_OPERATING_REVENUE = 'non_operating_revenue'
KEY_OPERATING_EXPENSE = 'operating_expense'
KEY_NON_OPERATING_EXPENSE = 'non_operating_expense'
KEY_BALANCE = 'balance'


def get_income_statement_data(current_period) -> dict:
    current_data = _invoice_statement_date_for_period(current_period)

    period_before = current_period.period_before
    if period_before:
        previous_data = _invoice_statement_date_for_period(period_before)
    else:
        previous_data = None
    
    return (previous_data, current_data,)


def union_account_slugs_across_income_statement_data(list_of_income_statements_data:list, key:str) -> set:
    # TODO: list comprehension this for moar speed
    account_slugs = set()
    for income_statement_data in list_of_income_statements_data:
        if not income_statement_data:
            continue
        for row in income_statement_data[key]['rows']:
            account_slugs.add(row['account']['slug'])
    return account_slugs


def _invoice_statement_date_for_period(period) -> dict:
    """ Get operating income, operating expenses, operating income,
        non-operating income, non-operating expenses, net income data
    """
    operating_accounts = (period.company.account_set
        .filter(type__in=Account.OPERATING_TYPES)
        .values('slug', 'name', 'number', 'type', 'is_contra', 'is_operating'))
    operating_accounts = {a['slug']:a for a in operating_accounts}

    operating_account_slugs = (period.company.account_set
        .filter(type__in=Account.OPERATING_TYPES, is_operating=True)
        .values_list('slug', flat=True))

    data = {
        KEY_OPERATING_REVENUE:{
            'rows':[],
            'rows_by_account':{},
            'total':0,
        },
        KEY_NON_OPERATING_REVENUE:{
            'rows':[],
            'rows_by_account':{},
            'total':0,
        },
        KEY_OPERATING_EXPENSE:{
            'rows':[],
            'rows_by_account':{},
            'total':0,
        },
        KEY_NON_OPERATING_EXPENSE:{
            'rows':[],
            'rows_by_account':{},
            'total':0,
        },
    }


    journal_entries = JournalEntry.objects.filter_for_adjusted_trial(period)
    journal_entry_lines = (JournalEntryLine.objects
        .filter(journal_entry__in=journal_entries, account__type__in=Account.OPERATING_TYPES)
        .values(
            "account__slug", "journal_entry__period__id", "type", "amount"))

    get_default_row = lambda: {
        JournalEntryLine.TYPE_DEBIT:0,
        JournalEntryLine.TYPE_CREDIT:0,
        KEY_BALANCE:0,
    }
    amounts_by_account = defaultdict(get_default_row)
    for jel in journal_entry_lines:
        account_slug = jel['account__slug']
        if jel['type'] == JournalEntryLine.TYPE_DEBIT:
            amounts_by_account[account_slug][JournalEntryLine.TYPE_DEBIT] += jel['amount']
        else:
            amounts_by_account[account_slug][JournalEntryLine.TYPE_CREDIT] += jel['amount']

    for account_slug in amounts_by_account:
        balance = get_dr_cr_balance(
            amounts_by_account[account_slug][JournalEntryLine.TYPE_DEBIT],
            amounts_by_account[account_slug][JournalEntryLine.TYPE_CREDIT])

        if balance == 0:
            continue
        
        account = operating_accounts[account_slug]
        row = {
            KEY_BALANCE:(balance * -1) if account['is_contra'] else balance,
            'account':account,
        }
        if account['type'] == Account.TYPE_REVENUE:
            if account['slug'] in operating_account_slugs:
                data[KEY_OPERATING_REVENUE]['rows'].append(row)
            else:
                data[KEY_NON_OPERATING_REVENUE]['rows'].append(row)
    
        elif account['type'] == Account.TYPE_EXPENSE:
            if account['slug'] in operating_account_slugs:
                data[KEY_OPERATING_EXPENSE]['rows'].append(row)
            else:
                data[KEY_NON_OPERATING_EXPENSE]['rows'].append(row)
        else:
            raise NotImplementedError()

    for key in data:
        data[key]['rows'].sort(key=lambda r: r['account']['number'])
        data[key]['rows_by_account'] = {r['account']['slug']:r for r in data[key]['rows']}
        data[key]['total'] = sum(row[KEY_BALANCE] for row in data[key]['rows'])
    
    return data

KEY_TOTAL_ASSETS = 'total_assets'
KEY_TOTAL_LIABILITIES = 'total_liabilities'
KEY_TOTAL_EQUITY = 'total_equity'
KEY_TOTAL_LIABILITIES_AND_EQUITY = 'total_liabilities_and_equity'
KEY_CURR_ASSET = 'current_assets'
KEY_NON_CURR_ASSET = 'non_current_asset'
KEY_CURR_LIABILITY = 'current_liability'
KEY_NON_CURR_LIABILITY = 'non_current_liability'
KEY_EQUITY = 'equity'

def get_balance_sheet_data(current_period):
    journal_entries = JournalEntry.objects.filter_for_balance_sheet(
        current_period)
    journal_entry_lines = JournalEntryLine.objects.filter(
        journal_entry__in=journal_entries, account__type__in=Account.BALANCE_SHEET_TYPES)

    # Aggregate DR/CR amounts by Account
    get_default_row = lambda: {
        JournalEntryLine.TYPE_DEBIT:0,
        JournalEntryLine.TYPE_CREDIT:0,
        'balance':0,
        "account__type":None,
    }
    amounts_by_account = defaultdict(get_default_row)

    for jel in journal_entry_lines.values("account__slug", "account__type", "type", "amount"):
        account_slug = jel['account__slug']
        amounts_by_account[account_slug]["account__type"] = jel["account__type"]
        if jel['type'] == JournalEntryLine.TYPE_DEBIT:
            amounts_by_account[account_slug][JournalEntryLine.TYPE_DEBIT] += jel['amount']
        elif jel['type'] == JournalEntryLine.TYPE_CREDIT:
            amounts_by_account[account_slug][JournalEntryLine.TYPE_CREDIT] += jel['amount']
        else:
            raise NotImplementedError()
    
    for account_slug in amounts_by_account:
        dr_amount = amounts_by_account[account_slug][JournalEntryLine.TYPE_DEBIT]
        cr_amount = amounts_by_account[account_slug][JournalEntryLine.TYPE_CREDIT]
        balance = get_dr_cr_balance(dr_amount, cr_amount)

        if cr_amount > dr_amount and amounts_by_account[account_slug]['account__type'] == Account.TYPE_ASSET:
            balance = force_negative(balance)
        elif cr_amount < dr_amount and amounts_by_account[account_slug]['account__type'] == Account.TYPE_LIABILITY:
            balance = force_negative(balance)

        amounts_by_account[account_slug]['balance'] = balance
    
    account_slugs = set(amounts_by_account.keys())
    accounts = Account.objects.filter(slug__in=account_slugs)

    data = {
        KEY_CURR_ASSET:{
            'rows':[],
            'total':0,
        },
        KEY_NON_CURR_ASSET:{
            'rows':[],
            'total':0,
        },
        KEY_CURR_LIABILITY:{
            'rows':[],
            'total':0,
        },
        KEY_NON_CURR_LIABILITY:{
            'rows':[],
            'total':0,
        },
        KEY_EQUITY:{
            'rows':[],
            'total':0,
        },
        KEY_TOTAL_ASSETS:0,
        KEY_TOTAL_LIABILITIES:0,
        KEY_TOTAL_EQUITY:0,
        KEY_TOTAL_LIABILITIES_AND_EQUITY:0,
    }

    # current assets
    for acc in (accounts
            .filter(type=Account.TYPE_ASSET, is_current=True)
            .order_by('number')
            .values("slug", "name", "number", "type", "is_contra", "is_current", "is_operating")):
    
        balance = amounts_by_account[acc['slug']]['balance']
        if balance == 0:
            continue
        data[KEY_CURR_ASSET]['total'] += balance
        data[KEY_TOTAL_ASSETS] += balance
        data[KEY_CURR_ASSET]['rows'].append({
            "account":acc,
            "balance":balance,
        })

    # non current assets
    for acc in (accounts
            .filter(type=Account.TYPE_ASSET, is_current=False)
            .order_by('number')
            .values("slug", "name", "number", "type", "is_contra", "is_current", "is_operating")):

        balance = amounts_by_account[acc['slug']]['balance']
        if balance == 0:
            continue
        data[KEY_NON_CURR_ASSET]['total'] += balance
        data[KEY_TOTAL_ASSETS] += balance
        data[KEY_NON_CURR_ASSET]['rows'].append({
            "account":acc,
            "balance":balance,
        })

    # current liabilities
    for acc in (accounts
            .filter(type=Account.TYPE_LIABILITY, is_current=True)
            .order_by('number')
            .values("slug", "name", "number", "type", "is_contra", "is_current", "is_operating")):
        balance = amounts_by_account[acc['slug']]['balance']
        if balance == 0:
            continue
        data[KEY_CURR_LIABILITY]['total'] += balance
        data[KEY_TOTAL_LIABILITIES] += balance
        data[KEY_TOTAL_LIABILITIES_AND_EQUITY] += balance
        data[KEY_CURR_LIABILITY]['rows'].append({
            "account":acc,
            "balance":balance,
        })

    # non current liabilities
    for acc in (accounts
            .filter(type=Account.TYPE_LIABILITY, is_current=False)
            .order_by('number').values("slug", "name", "number", "type", "is_contra", "is_current", "is_operating")):

        balance = amounts_by_account[acc['slug']]['balance']
        if balance == 0:
            continue
        data[KEY_NON_CURR_LIABILITY]['total'] += balance
        data[KEY_TOTAL_LIABILITIES] += balance
        data[KEY_TOTAL_LIABILITIES_AND_EQUITY] += balance
        data[KEY_NON_CURR_LIABILITY]['rows'].append({
            "account":acc,
            "balance":balance,
        })

    # equity
    for acc in (accounts
            .filter(type=Account.TYPE_EQUITY)
            .order_by('number')
            .values("slug", "name", "number", "type", "is_contra", "is_current", "is_operating")):

    
        balance = amounts_by_account[acc['slug']]['balance']
        if balance == 0:
            continue
        data[KEY_EQUITY]['total'] += balance
        data[KEY_TOTAL_EQUITY] += balance
        data[KEY_TOTAL_LIABILITIES_AND_EQUITY] += balance
        data[KEY_EQUITY]['rows'].append({
            "account":acc,
            "balance":balance,
        })
    
    return data


def get_retained_earnings_data(current_period):

    data = {
        'retained_earnings_start':0,
        'retained_earnings_end':0,
        'dividends':0,
        'net_income':0,
    }

    # get Retained Earnings balance through current period start
    curr_re_jels_start = (JournalEntryLine.objects
        .filter(
            journal_entry__period__in=get_company_periods_up_to_and_excluding(current_period),
            account__tag=Account.TAG_RETAINED_EARNINGS)
        .values("type", "amount"))

    for jel in curr_re_jels_start:
        if jel['type'] == JournalEntryLine.TYPE_CREDIT:    # equity account has CR balance
            data['retained_earnings_start'] += jel['amount']
        elif jel['type'] == JournalEntryLine.TYPE_DEBIT:
            data['retained_earnings_start'] -= jel['amount']


    # get Retained Earnings balance through current period end
    curr_re_jels_end = (JournalEntryLine.objects
        .filter(
            journal_entry__period__in=get_company_periods_up_to(current_period),
            account__tag=Account.TAG_RETAINED_EARNINGS)
        .values("type", "amount"))

    for jel in curr_re_jels_end:
        if jel['type'] == JournalEntryLine.TYPE_CREDIT:     # equity account has CR balance
            data['retained_earnings_end'] += jel['amount']
        elif jel['type'] == JournalEntryLine.TYPE_DEBIT:
            data['retained_earnings_end'] -= jel['amount']

    # Given net income, retained earnings start/end, calculate dividends
    income_data = _invoice_statement_date_for_period(current_period)
    total_revenue = income_data[KEY_OPERATING_REVENUE]['total'] + income_data[KEY_NON_OPERATING_REVENUE]['total']
    total_expenses = income_data[KEY_OPERATING_EXPENSE]['total'] + income_data[KEY_NON_OPERATING_EXPENSE]['total']
    net_income = total_revenue - total_expenses
    data['net_income'] = net_income

    dividends = (data['retained_earnings_start'] + net_income) - data['retained_earnings_end']
    data['dividends'] = dividends

    return data

KEY_CASHFLOW_OPERATIONS = 'operations'
KEY_CASHFLOW_INVESTMENTS = 'investments'
KEY_CASHFLOW_FINANCING = 'finances'
def get_period_cash_flow_worksheet(period) -> tuple:
    """ Determine whether or not a period requires a cashflow worksheet to be
        completed before a statement of cash flows can be assembled.

        A worksheet is required if the period has a 1 or more journal entries that
        touches both CASH as well as a Non-Cash Current asset. A worksheet is needed in this
        case because transactions that touch CASH as well as a Non-Cash Current asset
        could be classified as activity from operations, OR activity from Investing.
        We can't know for sure so we need user input via a cashflow worksheet if any
        of these transactions exist for the period.
    """
    entries_analyzed = Counter()
    company = period.company

    # Fetch Account IDs by catagory
    cash_accounts = (Account.objects
        .filter(
            company=company, tag=Account.TAG_CASH, type=Account.TYPE_ASSET,
            is_current=True, is_contra=False)
        .values_list("id", flat=True))

    non_cash_current_asset_accounts = (Account.objects
        .filter(
            company=company, type=Account.TYPE_ASSET, is_current=True)
        .filter(~Q(tag=Account.TAG_CASH))
        .values_list("id", flat=True))

    non_current_asset_accounts = (Account.objects
        .filter(
            company=company, type=Account.TYPE_ASSET, is_current=False)
        .filter(~Q(tag=Account.TAG_CASH))
        .values_list("id", flat=True))
    
    
    liability_accounts = (Account.objects
        .filter(
            company=company, type=Account.TYPE_EXPENSE)
        .values_list("id", flat=True))

    equity_accounts = (Account.objects
        .filter(
            company=company, type=Account.TYPE_EXPENSE)
        .values_list("id", flat=True))

    income_statement_accounts = (Account.objects
        .filter(
            company=company, type__in=Account.OPERATING_TYPES)
        .values_list("id", flat=True))

    # Fetch journal entry ids that involve a cash account
    cash_journal_entries = (JournalEntryLine.objects
        .filter(account_id__in=cash_accounts)
        .values_list("journal_entry_id", flat=True))
    
    jounral_entries = JournalEntry.objects.filter(id__in=cash_journal_entries).values("id", "date", "memo", "display_id", "slug")
    jounral_entries = {je['id']:je for je in jounral_entries}

    # Fetch all jounral entry lines associated with
    journal_entry_lines = (JournalEntryLine.objects
        .filter(journal_entry_id__in=cash_journal_entries)
        .values("account_id", "account__name", "account__number", "account__tag", "journal_entry_id", "type", "amount"))
    
    # group up accounts by the jounral entries they fall into
    jounral_entries_data = {}
    for jel in journal_entry_lines:
        je_id = jel['journal_entry_id']
        if je_id not in jounral_entries_data:
            jounral_entries_data[je_id] = {
                JournalEntryLine.TYPE_DEBIT:[],
                JournalEntryLine.TYPE_CREDIT:[],
                "all_accounts":[],
                'journal_entry_lines':[]
            }
        jounral_entries_data[je_id][jel['type']].append(jel['account_id'])
        jounral_entries_data[je_id]['all_accounts'].append(jel['account_id'])
        jounral_entries_data[je_id]['journal_entry_lines'].append(jel)
    
    # analyze 
    worksheet = []
    for je_id, accounts in jounral_entries_data.items():

        cash_dr_total = sum(jel['amount'] for jel in accounts['journal_entry_lines'] if jel['type'] == JournalEntryLine.TYPE_DEBIT and jel['account_id'] in cash_accounts)
        cash_cr_total = sum(jel['amount'] for jel in accounts['journal_entry_lines'] if jel['type'] == JournalEntryLine.TYPE_CREDIT and jel['account_id'] in cash_accounts)
        cash_to_allocate = get_dr_cr_balance(cash_dr_total, cash_cr_total)

        worksheet_row = {
            'debit_entries':[jel for jel in accounts['journal_entry_lines'] if jel['type'] == JournalEntryLine.TYPE_DEBIT],
            'credit_entries':[jel for jel in accounts['journal_entry_lines'] if jel['type'] == JournalEntryLine.TYPE_CREDIT],
            'memo':jounral_entries[je_id]['memo'],
            'date':jounral_entries[je_id]['date'],
            'display_id':jounral_entries[je_id]['display_id'],
            'slug':jounral_entries[je_id]['slug'],
            'cash_to_allocate':cash_to_allocate,
            'auto_complete':{
                'investments':0,
                'operations':0,
                'finances':0,
            },
        }

        worksheet.append(worksheet_row)
    
    return worksheet


        # # Attempt to automatically classify an entry as a use/source of cash related to either
        # # ops, investments, or financing.
        
        # # check which side of the JE has the cash account
        # cash_on_dr = any(acc_id in cash_accounts for acc_id in accounts[JournalEntryLine.TYPE_DEBIT])
        # cash_on_cr = any(acc_id in cash_accounts for acc_id in accounts[JournalEntryLine.TYPE_CREDIT])
        # cash_on_one_side = some([cash_on_dr, cash_on_cr])

        # # check if all DRs or all CRs are asset accounts
        # all_dr_assets = all(
        #         (acc_id in cash_accounts 
        #         or acc_id in non_cash_current_asset_accounts
        #         or acc_id in non_current_asset_accounts)
        #     for acc_id in accounts[JournalEntryLine.TYPE_DEBIT])
        # all_cr_assets = all(
        #         (acc_id in cash_accounts 
        #         or acc_id in non_cash_current_asset_accounts
        #         or acc_id in non_current_asset_accounts)
        #     for acc_id in accounts[JournalEntryLine.TYPE_CREDIT])
        
        # # check if all DRs or all CRs are liability/equity accounts
        # all_dr_liability_equity = all(
        #         (acc_id in liability_accounts 
        #         or acc_id in equity_accounts)
        #     for acc_id in accounts[JournalEntryLine.TYPE_DEBIT])
        # all_cr_liability_equity = all(
        #         (acc_id in liability_accounts 
        #         or acc_id in equity_accounts)
        #     for acc_id in accounts[JournalEntryLine.TYPE_CREDIT])

        # # check if all DRs or all CRs are operating accounts
        # all_dr_operating = all(acc_id in income_statement_accounts for acc_id in accounts[JournalEntryLine.TYPE_DEBIT])
        # all_cr_operating = all(acc_id in income_statement_accounts for acc_id in accounts[JournalEntryLine.TYPE_CREDIT])

        # # check if all DRs or all CRs are PPE
        # all_dr_ppe = all(acc_id in non_current_asset_accounts for acc_id in accounts[JournalEntryLine.TYPE_DEBIT])
        # all_cr_ppe = all(acc_id in non_current_asset_accounts for acc_id in accounts[JournalEntryLine.TYPE_CREDIT])

        
        # if cash_on_one_side and cash_on_dr and all_cr_liability_equity:
        #     entries_analyzed['auto_complete_ok'] += 1
        #     worksheet_row['auto_complete'] = "finances"
        #     worksheet.append(worksheet_row)
        # elif cash_on_one_side and cash_on_cr and all_dr_liability_equity:
        #     entries_analyzed['auto_complete_ok'] += 1
        #     worksheet_row['auto_complete'] = "finances"
        #     worksheet.append(worksheet_row)
        
        # elif cash_on_one_side and cash_on_dr and all_cr_operating:
        #     entries_analyzed['auto_complete_ok'] += 1
        #     worksheet_row['auto_complete'] = "operations"
        #     worksheet.append(worksheet_row)
        # elif cash_on_one_side and cash_on_cr and all_dr_operating:
        #     entries_analyzed['auto_complete_ok'] += 1
        #     worksheet_row['auto_complete'] = "operations"
        #     worksheet.append(worksheet_row)

        # elif cash_on_one_side and cash_on_dr and all_cr_ppe:
        #     entries_analyzed['auto_complete_ok'] += 1
        #     worksheet_row['auto_complete'] = "investments"
        #     worksheet.append(worksheet_row)
        # elif cash_on_one_side and cash_on_cr and all_dr_ppe:
        #     entries_analyzed['auto_complete_ok'] += 1
        #     worksheet_row['auto_complete'] = "investments"
        #     worksheet.append(worksheet_row)        

        # else:
        #     # Failed to identify the classification
        #     entries_analyzed['auto_complete_failed'] += 1
        #     worksheet.append(worksheet_row)





def get_worksheet_page_data(period) -> dict:
    pass
