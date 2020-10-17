
from collections import defaultdict
import random
import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.http import HttpResponseNotAllowed, HttpResponse, HttpResponseBadRequest
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from api.models import Company, Account, Period, JournalEntry, JournalEntryLine, UserProfile
from api.models.account import DEFAULT_ACCOUNTS
from api.utils import (
    get_slug_from_account_activation_token,
    generate_slug,
    get_report_page_breadcrumbs,
    is_valid_slug
)
from api.lib import reports as reports_lib, company_export, email as email_lib
from api import utils
from website.forms import LoginForm, RegisterNewUser


def anon_landing(request):
    if request.user.is_authenticated:
        return redirect("app-landing")
    return render(request, "anon_landing.html", {
        'gallery_image':next(iter(sorted(utils.get_photo_gallery_images(), key=lambda a: random.random()))),
    })

@login_required
def app_main_menu(request):
    data = {
        'skip_moment_import':True,
    }
    return render(request, "app_main_menu.html", data)


@login_required
def app_landing(request):

    at_object_limit = request.user.userprofile.at_company_object_limit

    breadcrumbs = [
        {
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'companies',
        },
    ]
    data = {
        'skip_moment_import':True,
        'breadcrumbs':breadcrumbs,
        'at_object_limit':at_object_limit,
    }
    return render(request, "app_landing.html", data)


@login_required
def app_company(request, slug):
    company = get_object_or_404(Company, user=request.user, slug=slug)
    account_count = Account.objects.filter(company=company).count()
    period_count = Period.objects.filter(company=company).count()
    journal_entry_count = JournalEntry.objects.filter(period__company=company).count()
    breadcrumbs = [
        {
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'companies',
            'href':reverse("app-landing"),
        }, {
            'value':company.name,
            'elementid':'breadcrum-company-name',
        }
    ]
    data = {
        'company':company,
        'breadcrumbs':breadcrumbs,
        'account_count':account_count,
        'period_count':period_count,
        'journal_entry_count':journal_entry_count,
    }
    return render(request, "app_company.html", data)


@login_required
def app_periods(request, slug):
    company = get_object_or_404(Company, user=request.user, slug=slug)
    breadcrumbs = [
        {
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'companies',
            'href':reverse("app-landing"),
        }, {
            'value':company.name,
            'href':reverse("app-company", kwargs={'slug':company.slug}),
        }, {
            'value':'periods',
        }
    ]
    data = {
        'company':company,
        'breadcrumbs':breadcrumbs,
    }
    return render(request, "app_periods.html", data)


@login_required
def app_period_detail(request, slug):
    period = get_object_or_404(Period, company__user=request.user, slug=slug)
    try:
        last_je = period.journalentry_set.latest("date")
        default_date = last_je.date
    except JournalEntry.DoesNotExist:
        default_date = period.start
    company = period.company
    date_format = "%b %-d, %Y"
    breadcrumbs = [
        {
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'companies',
            'href':reverse("app-landing"),
        }, {
            'value':company.name,
            'href':reverse("app-company", kwargs={'slug':company.slug}),
        }, {
            'value':'periods',
            'href':reverse("app-period", kwargs={'slug':company.slug})
        }, {
            'value':f'{period.start.strftime(date_format)} -> {period.end.strftime(date_format)}',
        }
    ]
    has_closing_entries = period.journalentry_set.filter(is_closing_entry=True)
    has_adjusting_entries = period.journalentry_set.filter(is_adjusting_entry=True)
    data = {
        'period':period,
        'company':company,
        'default_date':default_date,
        'breadcrumbs':breadcrumbs,
        'include_select2':True,
        'has_closing_entries':has_closing_entries,
        'has_adjusting_entries':has_adjusting_entries,
    }
    return render(request, "app_period_detail.html", data)


@login_required
def app_jounral_entry_detail(request, slug):
    journal_entry = get_object_or_404(
        JournalEntry, slug=slug, period__company__user=request.user)
    period = journal_entry.period
    company = period.company
    date_format = "%b %-d, %Y"
    breadcrumbs = [
        {
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'companies',
            'href':reverse("app-landing"),
        }, {
            'value':company.name,
            'href':reverse("app-company", kwargs={'slug':company.slug}),
        }, {
            'value':'periods',
            'href':reverse("app-period", kwargs={'slug':company.slug})
        }, {
            'value':f'{period.start.strftime(date_format)} -> {period.end.strftime(date_format)}',
            'href':reverse("app-period-details", kwargs={'slug':period.slug})
        }, {
            'value':f'Jounral Entry {journal_entry.display_id}',
        }
    ]

    # TODO: do formatting in the browser.
    def _get_with_ix(array:list, ix:int):
        try:
            return array[ix]
        except IndexError:
            return None
    
    def _format_int(x:int):
        if not x:
            return x
        prefix = "+" if x > 0 else ""
        return prefix + "{:,}".format(x)
        
    # TODO: prepare this data in a separate function.
    analysis = reports_lib.get_journal_entry_impact_on_accounting_equation(journal_entry)
    analysis_rows = []
    ix = 0
    while True:
        if (not _get_with_ix(analysis['asset_rows'], ix)
            and not _get_with_ix(analysis['liability_rows'], ix)
            and not _get_with_ix(analysis['equity_rows'], ix)):
            break

        analysis_rows.append({
            'asset':_format_int(_get_with_ix(analysis['asset_rows'], ix)),
            'liability':_format_int(_get_with_ix(analysis['liability_rows'], ix)),
            'equity':_format_int(_get_with_ix(analysis['equity_rows'], ix)),
        })
        ix += 1
    
    data = {
        'journal_entry':journal_entry,
        'period':period,
        'company':company,
        'breadcrumbs':breadcrumbs,
        'journal_entry_analysis_rows':analysis_rows,
        'delta_assets':_format_int(analysis['delta_assets']),
        'delta_liabilities':_format_int(analysis['delta_liabilities']),
        'delta_equity':_format_int(analysis['delta_equity']),
    }
    return render(request, "journal_entry_details.html", data)


@login_required
def app_company_accounts(request, slug):
    company = get_object_or_404(
        Company, user=request.user, slug=slug)

    breadcrumbs = [
        {
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'companies',
            'href':reverse("app-landing"),
        }, {
            'value':company.name,
            'href':reverse("app-company", kwargs={'slug':company.slug}),
        }, {
            'value':'accounts',
        }
    ]
    data = {
        'company':company,
        'breadcrumbs':breadcrumbs,
        'tags':Account.ACCOUNT_TAGS_CHOICES,
    }
    return render(request, "app_company_accounts.html", data)


@login_required
def app_period_je_csv(request, slug):
    period = get_object_or_404(Period, company__user=request.user, slug=slug)
    journal_entries = JournalEntry.objects.filter(period=period)
    try:
        repeat_values = bool(int(request.GET.get("printrepeats", 0)))
    except Exception:
        repeat_values = False
    try:
        past_values = bool(int(request.GET.get("past", 0)))
    except Exception:
        past_values = False
    try:
        future_values = bool(int(request.GET.get("future", 0)))
    except Exception:
        future_values = False
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="jounral-entries-{slug}.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "journal entry number", "closing Entry", "adjusting entry", "date", "memo", "account name", "account number",
        "debit", "credit", "magnitude",
    ])

    journal_entry_lines = JournalEntryLine.objects.filter(journal_entry__in=journal_entries)
    journal_entry_lines = journal_entry_lines.values(
        "journal_entry_id", "account_id", "amount", "type")
    
    jel_map = defaultdict(lambda:{
        'dr_lines':[],
        'cr_lines':[],
    })
    for jel in journal_entry_lines:
        if jel['type'] == JournalEntryLine.TYPE_DEBIT:
            jel_map[jel['journal_entry_id']]['dr_lines'].append(jel)
        elif jel['type'] == JournalEntryLine.TYPE_CREDIT:
            jel_map[jel['journal_entry_id']]['cr_lines'].append(jel)

    accounts = Account.objects.filter(company=period.company)
    accounts = accounts.values("id", "name", "number")
    acc_map = {a['id']:a for a in accounts}

    journal_entries = journal_entries.order_by("display_id").values(
        "id", "date", "memo", "display_id", "is_adjusting_entry", "is_closing_entry")

    for je in journal_entries:
        dr_jels = sorted(jel_map[je['id']]['dr_lines'], key=lambda jel: acc_map[jel['account_id']]['number'])
        cr_jels = sorted(jel_map[je['id']]['cr_lines'], key=lambda jel: acc_map[jel['account_id']]['number'])
        for dr_jel in dr_jels:
            writer.writerow([
                je['display_id'], je['is_closing_entry'], je['is_adjusting_entry'],
                je['date'], je['memo'],
                acc_map[dr_jel['account_id']]['name'], acc_map[dr_jel['account_id']]['number'],
                dr_jel['amount'], 0, dr_jel['amount']
            ])
        for cr_jel in cr_jels:
            writer.writerow([
                je['display_id'], je['is_closing_entry'], je['is_adjusting_entry'],
                je['date'], je['memo'],
                acc_map[cr_jel['account_id']]['name'], acc_map[cr_jel['account_id']]['number'],
                0, cr_jel['amount'], cr_jel['amount']
            ])
    
    return response
    


@login_required
def app_company_accounts_csv(request, slug):
    company = get_object_or_404(
        Company, user=request.user, slug=slug)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="company-accounts{slug}.csv"'
    writer = csv.writer(response)
    writer.writerow(["name", "number", "type", "is_contra", "is_current", "is_operating", "tag"])

    for row in company.account_set.values_list(
        "name", "number", "type", "is_contra", "is_current", "is_operating", "tag"):

        writer.writerow(row)

    return response



@login_required
def app_account_details(request, slug):
    account = get_object_or_404(
        Account, company__user=request.user, slug=slug)
    company = account.company

    periods_ids = (JournalEntryLine.objects
        .filter(account=account)
        .values_list("journal_entry__period_id", flat=True)
        .distinct())
    periods = Period.objects.filter(id__in=periods_ids).order_by("-start")

    breadcrumbs = [
        {
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'companies',
            'href':reverse("app-landing"),
        }, {
            'value':company.name,
            'href':reverse("app-company", kwargs={'slug':company.slug}),
        }, {
            'value':'accounts',
            'href':reverse("app-accounts", kwargs={'slug':company.slug}),
        }, {
            'value':account.name,
        }
    ]
    data = {
        'company':company,
        'periods':periods,
        'account':account,
        'breadcrumbs':breadcrumbs,
        'tags':Account.ACCOUNT_TAGS_CHOICES,
        'available_tag_options':account.available_tag_options,
    }
    return render(request, "app_account_details.html", data)


@login_required
def app_company_add_default_accounts(request, slug):
    company = get_object_or_404(
        Company, user=request.user, slug=slug)
    
    if company.account_set.exists():
        return redirect('app-accounts', slug=company.slug)

    breadcrumbs = [
        {
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'companies',
            'href':reverse("app-landing"),
        }, {
            'value':company.name,
            'href':reverse("app-company", kwargs={'slug':company.slug}),
        }, {
            'value':'default accounts',
        }
    ]
    default_accounts = [
        {
            'type':a[0],
            'is_current':a[1],
            'is_contra':a[2],
            'is_operating':a[3],
            'number':a[4],
            'name':a[5],
            'tag':Account.ACCOUNT_TAG_NAME_DICT[a[6]] if a[6] else None,
        } for a in DEFAULT_ACCOUNTS
    ]
    data = {
        'company':company,
        'breadcrumbs':breadcrumbs,
        'default_accounts':sorted(default_accounts, key=lambda r:r['number']),
    }
    return render(request, "app_company_add_default_accounts.html", data)


@login_required
def app_profile(request):
    breadcrumbs = [
        {
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'settings',
        },
    ]
    data = {
        'breadcrumbs':breadcrumbs,
        'skip_moment_import':True,
    }
    return render(request, "app_profile.html", data)


@login_required
def app_export_company(request, slug):
    company = get_object_or_404(Company, slug=slug, user=request.user)

    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="company-export-{slug}.txt"'
    
    data = company_export.export_company_to_jwt(company)
    response.write(company_export.sign_comapny_export_jwt(data))

    return response


@login_required
def app_export_tools_menu(request):
    breadcrumbs = [
        {
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'export tools',
        },
    ]
    data = {
        'breadcrumbs':breadcrumbs,
    }
    return render(request, "export_tools_menu.html", data)




@login_required
def app_import_company(request):
    # Check object limit.
    at_object_limit = request.user.userprofile.at_company_object_limit

    breadcrumbs = [
        {
            'value':'menu',
            'href':reverse("app-main-menu")
        }, {
            'value':'companies',
            'href':reverse("app-landing"),
        }, {
            'value':'Import a Company',
        },
    ]
    data = {
        'breadcrumbs':breadcrumbs,
        'skip_moment_import':True,
        'at_object_limit':at_object_limit,
    }
    return render(request, "app_company_import.html", data)


# REPORT PAGES

@login_required
def t_account(request, period_slug, account_slug):
    current_period = get_object_or_404(
        Period, company__user=request.user, slug=period_slug)
    account = get_object_or_404(Account, company=current_period.company, slug=account_slug)

    (rows,
    start_balance,
    end_balance,
    prev_dr_total,
    prev_cr_total,
    curr_dr_total,
    curr_cr_total,) = reports_lib.get_t_account_data_for_account(account, current_period)

    balance_change = f'({format(abs(end_balance - start_balance), ",")})' if end_balance < start_balance else format(end_balance - start_balance, ",")

    breadcrumbs = get_report_page_breadcrumbs(current_period, f"{account.name} T-Account")
    data = {
        'breadcrumbs':breadcrumbs,
        'account':account,
        'period':current_period,
        'start_balance':start_balance,
        'end_balance':end_balance,
        'balance_change':balance_change,
        'prev_dr_total':prev_dr_total,
        'prev_cr_total':prev_cr_total,
        'curr_dr_total':curr_dr_total,
        'curr_cr_total':curr_cr_total,
        't_account_rows':rows,
    }
    return render(request, "app_report_t_account.html", data)


@login_required
def t_account_csv(request, period_slug, account_slug):
    current_period = get_object_or_404(
        Period, company__user=request.user, slug=period_slug)
    account = get_object_or_404(Account, company=current_period.company, slug=account_slug)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="taccount-{account_slug}-{period_slug}.csv"')
    writer = csv.writer(response)
    writer.writerow([
        "Entry Date", "Journal Entry Id", "Closing Entry", "Adjusting Entry", "Debit Amount", "Credit Amount",
    ])

    (rows,
    start_balance,
    end_balance,
    prev_dr_total,
    prev_cr_total,
    curr_dr_total,
    curr_cr_total,) = reports_lib.get_t_account_data_for_account(account, current_period)

    for row in rows:
        writer.writerow([
            row['journal_entry__date'], row['journal_entry__display_id'],
            row['journal_entry__is_closing_entry'],
            row['journal_entry__is_adjusting_entry'],
            row['amount'] if row['type'] == JournalEntryLine.TYPE_DEBIT else 0,
            row['amount'] if row['type'] == JournalEntryLine.TYPE_CREDIT else 0,
        ])

    return response


@login_required
def trial_balance(request, slug):
    current_period = get_object_or_404(
        Period, company__user=request.user, slug=slug)

    (rows,
    total_company_unadj_dr,
    total_company_unadj_cr,
    total_company_adj_dr,
    total_company_adj_cr,) = reports_lib.get_trial_balance_data(current_period)

    breadcrumbs = get_report_page_breadcrumbs(current_period, "Trial Balance")
    data = {
        'period':current_period,
        'breadcrumbs':breadcrumbs,
        'trial_balance_rows':rows,
        'total_company_unadj_dr':total_company_unadj_dr,
        'total_company_unadj_cr':total_company_unadj_cr,
        'total_company_adj_dr':total_company_adj_dr,
        'total_company_adj_cr':total_company_adj_cr,
    }
    return render(request, "app_report_trial_balance.html", data)


@login_required
def trial_balance_csv(request, slug):
    current_period = get_object_or_404(
        Period, company__user=request.user, slug=slug)

    (rows,
    total_company_unadj_dr,
    total_company_unadj_cr,
    total_company_adj_dr,
    total_company_adj_cr,) = reports_lib.get_trial_balance_data(current_period)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="trial-balance-{generate_slug(None)}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'account number', 'account name',
        'unadjusted debit balance', 'unadjusted credit balance',
        'adjusted debit balance', 'adjusted credit balance',
    ])
    for row in rows:
        writer.writerow([
            row['account']['number'], row['account']['name'],
            row['unadj_dr_bal'], row['unadj_cr_bal'],
            row['adj_dr_bal'], row['adj_cr_bal'],
        ])

    return response


@login_required
def income_statement(request, slug):
    current_period = get_object_or_404(
        Period, company__user=request.user, slug=slug)

    breadcrumbs = get_report_page_breadcrumbs(current_period, "Income Statement")

    (previous_is_data,
    current_is_data) = reports_lib.get_income_statement_data(current_period)

    # union accounts accross mulple periods
    operating_revenue_accounts = reports_lib.union_account_slugs_across_income_statement_data(
        [current_is_data, previous_is_data], reports_lib.KEY_OPERATING_REVENUE)
    non_operating_revenue_accounts = reports_lib.union_account_slugs_across_income_statement_data(
        [current_is_data, previous_is_data], reports_lib.KEY_NON_OPERATING_REVENUE)
    operating_expense_accounts = reports_lib.union_account_slugs_across_income_statement_data(
        [current_is_data, previous_is_data], reports_lib.KEY_OPERATING_EXPENSE)
    cogs_expense_accounts = reports_lib.union_account_slugs_across_income_statement_data(
        [current_is_data, previous_is_data], reports_lib.KEY_COST_OF_GOODS_SOLD)
    non_operating_expense_accounts = reports_lib.union_account_slugs_across_income_statement_data(
        [current_is_data, previous_is_data], reports_lib.KEY_NON_OPERATING_EXPENSE)

    operating_revenue_accounts = Account.objects.filter(slug__in=operating_revenue_accounts).order_by("number")
    non_operating_revenue_accounts = Account.objects.filter(slug__in=non_operating_revenue_accounts).order_by("number")
    operating_expense_accounts = Account.objects.filter(slug__in=operating_expense_accounts).order_by("number")
    cost_of_goods_sold_expense_accounts = Account.objects.filter(slug__in=cogs_expense_accounts).order_by("number")
    non_operating_expense_accounts = Account.objects.filter(slug__in=non_operating_expense_accounts).order_by("number")


    def _get_amount_info_from_is_data(rows, account):
        try:
            return next(r['balance'] for r in rows if r['account']['slug'] == account.slug)
        except StopIteration:
            return None

    rows = []

    # Operating
    # Operating Income
    if operating_revenue_accounts.exists():
        rows.append({
            'padding':1,
            'bold':True,
            'col1value':"Operating Revenue",
        })
        for account in operating_revenue_accounts:
            rows.append({
                'padding':3,
                'col1value':f"({account.number}) {account.name}",
                'col2value':_get_amount_info_from_is_data(
                    previous_is_data[reports_lib.KEY_OPERATING_REVENUE]['rows'], account) if previous_is_data else None,
                'col3value':_get_amount_info_from_is_data(
                    current_is_data[reports_lib.KEY_OPERATING_REVENUE]['rows'], account),
            })

        rows.append({
            'border':'border-top',
            'padding':4,
            'col1value':"Total Operating Revenue",
            'col2value':(
                previous_is_data[reports_lib.KEY_OPERATING_REVENUE]['total'] if previous_is_data else None),
            'col3value':(
                current_is_data[reports_lib.KEY_OPERATING_REVENUE]['total']),
        })

    # Cost of Goods Sold and gross profit
    if cost_of_goods_sold_expense_accounts.exists():
        rows.append({
            'new_section':True,
            'padding':1,
            'bold':True,
            'col1value':"Cost of Goods Sold",
        })
        for account in cost_of_goods_sold_expense_accounts:
            rows.append({
                'padding':3,
                'col1value':f"({account.number}) {account.name}",
                'col2value':_get_amount_info_from_is_data(
                    previous_is_data[reports_lib.KEY_COST_OF_GOODS_SOLD]['rows'], account) if previous_is_data else None,
                'col3value':_get_amount_info_from_is_data(
                    current_is_data[reports_lib.KEY_COST_OF_GOODS_SOLD]['rows'], account),
            })

        rows.append({
            'border':'border-top',
            'padding':4,
            'col1value':"Gross Profit",
            'col2value':(
                previous_is_data[reports_lib.KEY_OPERATING_REVENUE]['total'] - previous_is_data[reports_lib.KEY_COST_OF_GOODS_SOLD]['total'] if previous_is_data else None),
            'col3value':(
                current_is_data[reports_lib.KEY_OPERATING_REVENUE]['total'] - current_is_data[reports_lib.KEY_COST_OF_GOODS_SOLD]['total']),
        })
    

    # Operating Expenses
    if operating_expense_accounts.exists():
        rows.append({
            'new_section':True,
            'padding':1,
            'bold':True,
            'col1value':"Operating Expenses",
        })
        for account in operating_expense_accounts:
            rows.append({
                'padding':3,
                'col1value':f"({account.number}) {account.name}",
                'col2value':_get_amount_info_from_is_data(
                    previous_is_data[reports_lib.KEY_OPERATING_EXPENSE]['rows'], account) if previous_is_data else None,
                'col3value':_get_amount_info_from_is_data(
                    current_is_data[reports_lib.KEY_OPERATING_EXPENSE]['rows'], account),
            })

        rows.append({
            'border':'border-top',
            'padding':4,
            'col1value':"Total Operating Expenses",
            'col2value':(
                (previous_is_data[reports_lib.KEY_OPERATING_EXPENSE]['total'] + previous_is_data[reports_lib.KEY_COST_OF_GOODS_SOLD]['total']) if previous_is_data else None),
            'col3value':(
                current_is_data[reports_lib.KEY_OPERATING_EXPENSE]['total'] + current_is_data[reports_lib.KEY_COST_OF_GOODS_SOLD]['total']),
        })

        operating_income_row = {
            'padding':4,
            'border':'border-top',
            'col1value':"Operating Income",
            "col3value": (
                current_is_data[reports_lib.KEY_OPERATING_REVENUE]['total']
                - (current_is_data[reports_lib.KEY_OPERATING_EXPENSE]['total'] + current_is_data[reports_lib.KEY_COST_OF_GOODS_SOLD]['total'])
            )
        }
        if previous_is_data:
            operating_income_row['col2value'] = (
                previous_is_data[reports_lib.KEY_OPERATING_REVENUE]['total']
                - (previous_is_data[reports_lib.KEY_OPERATING_EXPENSE]['total'] + previous_is_data[reports_lib.KEY_COST_OF_GOODS_SOLD]['total'])
            )
        rows.append(operating_income_row)


    # Non Operating
    # Non Operating Income
    if non_operating_revenue_accounts.exists():
        rows.append({
            'new_section':True,
            'padding':1,
            'bold':True,
            'col1value':"Non-Operating Revenue",
        })
        for account in non_operating_revenue_accounts:
            rows.append({
                'padding':3,
                'col1value':f"({account.number}) {account.name}",
                'col2value':_get_amount_info_from_is_data(
                    previous_is_data[reports_lib.KEY_NON_OPERATING_REVENUE]['rows'], account) if previous_is_data else None,
                'col3value':_get_amount_info_from_is_data(
                    current_is_data[reports_lib.KEY_NON_OPERATING_REVENUE]['rows'], account),
            })

        rows.append({
            'border':'border-top',
            'padding':4,
            'col1value':"Total Non-Operating Revenue",
            'col2value':(
                previous_is_data[reports_lib.KEY_NON_OPERATING_REVENUE]['total'] if previous_is_data else None),
            'col3value':(
                current_is_data[reports_lib.KEY_NON_OPERATING_REVENUE]['total']),
        })
    

    # Non Operating
    # Non Operating Expenses
    if non_operating_expense_accounts.exists():
        rows.append({
            'new_section':True,
            'padding':1,
            'bold':True,
            'col1value':"Non-Operating Expenses",
        })
        for account in non_operating_expense_accounts:
            rows.append({
                'padding':3,
                'col1value':f"({account.number}) {account.name}",
                'col2value':_get_amount_info_from_is_data(
                    previous_is_data[reports_lib.KEY_NON_OPERATING_EXPENSE]['rows'], account) if previous_is_data else None,
                'col3value':_get_amount_info_from_is_data(
                    current_is_data[reports_lib.KEY_NON_OPERATING_EXPENSE]['rows'], account),
            })

        rows.append({
            'border':'border-top',
            'padding':4,
            'col1value':"Total Non-Operating Expenses",
            'col2value':(
                previous_is_data[reports_lib.KEY_NON_OPERATING_EXPENSE]['total'] if previous_is_data else None),
            'col3value':(
                current_is_data[reports_lib.KEY_NON_OPERATING_EXPENSE]['total']),
        })


        non_operating_income_row = {
            'padding':4,
            'border':'border-top',
            'col1value':"Non-Operating Income",
            "col3value": (
                current_is_data[reports_lib.KEY_NON_OPERATING_REVENUE]['total']
                - current_is_data[reports_lib.KEY_NON_OPERATING_EXPENSE]['total']
            )
        }
        if previous_is_data:
            non_operating_income_row['col2value'] = (
                previous_is_data[reports_lib.KEY_NON_OPERATING_REVENUE]['total']
                - previous_is_data[reports_lib.KEY_NON_OPERATING_EXPENSE]['total']
            )
        rows.append(non_operating_income_row)


        net_income_row = {
            'new_section':True,
            'padding':4,
            'border':'border-top',
            'col1value':"Net Income",
            "col3value": (
                (current_is_data[reports_lib.KEY_OPERATING_REVENUE]['total']
                + current_is_data[reports_lib.KEY_NON_OPERATING_REVENUE]['total'])
                - (current_is_data[reports_lib.KEY_OPERATING_EXPENSE]['total']
                + current_is_data[reports_lib.KEY_COST_OF_GOODS_SOLD]['total']
                + current_is_data[reports_lib.KEY_NON_OPERATING_EXPENSE]['total'])
            )
        }
        if previous_is_data:
            net_income_row['col2value'] = (
                (previous_is_data[reports_lib.KEY_OPERATING_REVENUE]['total']
                + previous_is_data[reports_lib.KEY_NON_OPERATING_REVENUE]['total'])
                - (previous_is_data[reports_lib.KEY_OPERATING_EXPENSE]['total']
                + previous_is_data[reports_lib.KEY_COST_OF_GOODS_SOLD]['total']
                + previous_is_data[reports_lib.KEY_NON_OPERATING_EXPENSE]['total'])
            )
        rows.append(net_income_row)




    data = {
        'rows':rows,
        'current_period':current_period,
        'previous_period':current_period.period_before,
        'breadcrumbs':breadcrumbs,
    }
    return render(request, "app_report_income_statement.html", data)


@login_required
def balance_sheet(request, slug):
    current_period = get_object_or_404(
        Period, company__user=request.user, slug=slug)
    
    balance_sheet_data = reports_lib.get_balance_sheet_data(current_period)

    breadcrumbs = get_report_page_breadcrumbs(current_period, "Balance Sheet")
    is_balanced = balance_sheet_data.get("total_assets") == balance_sheet_data.get("total_liabilities_and_equity")
    data = {
        'is_balanced':is_balanced,
        'balance_sheet_data':balance_sheet_data,
        'current_period':current_period,
        'breadcrumbs':breadcrumbs,
        'period':current_period,
    }
    return render(request, "app_report_balance_sheet.html", data)


@login_required
def retained_earnings(request, slug):
    current_period = get_object_or_404(
        Period, company__user=request.user, slug=slug)
    
    has_retained_earnings_account = Account.objects.filter(
        company=current_period.company, tag=Account.TAG_RETAINED_EARNINGS).exists()
    
    retained_earnings_data = reports_lib.get_retained_earnings_data(current_period)

    breadcrumbs = get_report_page_breadcrumbs(current_period, "Retained Earnings")
    data = {
        'period':current_period,
        'has_retained_earnings_account':has_retained_earnings_account,
        'retained_earnings_data':retained_earnings_data,
        'breadcrumbs':breadcrumbs,
    }
    return render(request, "app_report_retained_earnings.html", data)


@login_required
def statement_of_cash_flows_worksheet(request, slug):
    current_period = get_object_or_404(
        Period, company__user=request.user, slug=slug)
    company = current_period.company

    if not company.account_set.filter(
        type=Account.TYPE_ASSET,
        is_current=True,
        is_contra=False,
        tag=Account.TAG_CASH).exists():

        breadcrumbs = get_report_page_breadcrumbs(current_period, "Cash Flow Worksheet")
        data = {
            'period':current_period,
            'breadcrumbs':breadcrumbs,
        }

        return render(request, "app_report_cash_flow_error.html", data)


    cash_flow_worksheet = current_period.cash_flow_worksheet
    is_complete = cash_flow_worksheet and cash_flow_worksheet.in_sync

    worksheet = reports_lib.get_period_cash_flow_worksheet(current_period)
    breadcrumbs = get_report_page_breadcrumbs(current_period, "Cash Flow Worksheet")
    data = {
        'is_complete':is_complete,
        'period':current_period,
        'breadcrumbs':breadcrumbs,
        'worksheet':worksheet,
        'has_cash_account':company.account_set.filter(tag=Account.TAG_CASH).exists(),
    }
    return render(request, "app_report_cash_flow_worksheet.html", data)


@login_required
def statement_of_cash_flows(request, slug):
    current_period = get_object_or_404(
        Period, company__user=request.user, slug=slug)
    cash_flow_worksheet = current_period.cash_flow_worksheet
    
    # Redirect to the cashflow worksheet if one does not exist, or it's not in sync
    if not cash_flow_worksheet:
        return redirect("app-cash-flow-worksheet", slug=slug)
    if not cash_flow_worksheet.in_sync:
        cash_flow_worksheet.delete()
        return redirect("app-cash-flow-worksheet", slug=slug)

    if not current_period.company.account_set.filter(
        type=Account.TYPE_ASSET,
        is_current=True,
        is_contra=False,
        tag=Account.TAG_CASH).exists():

        breadcrumbs = get_report_page_breadcrumbs(current_period, "Cash Flow Statement")
        data = {
            'period':current_period,
            'breadcrumbs':breadcrumbs,
        }

        return render(request, "app_report_cash_flow_error.html", data)


    cashflow_data = reports_lib.get_statement_of_cash_flows_data(current_period)
    breadcrumbs = get_report_page_breadcrumbs(current_period, "Cash Flow Statement")
    data = {
        'period':current_period,
        'breadcrumbs':breadcrumbs,
        'cashflow_data':cashflow_data,
    }
    return render(request, "app_report_cash_flow_statement.html", data)


# END OF REPORT PAGES


def login_user(request):
    if request.method == 'GET':
        return redirect("anon-landing")

    if request.user.is_authenticated:
        return HttpResponseNotAllowed()

    form = LoginForm(request.POST)
    if not form.is_valid():
        data = {
            "loginerror":"invalid email/password",
        }
        return render(request, 'anon_landing.html', data)
    
    user = authenticate(
        request, 
        username=form.cleaned_data['email'], 
        password=form.cleaned_data['password'])

    if user is not None:
        login(request, user)
        return redirect('app-landing')
    else:
        data = {
            "loginerror":"invalid email/password",
            "loginemail":form.cleaned_data['email'],
        }
        return render(request, 'anon_landing.html', data)


@api_view(['POST'])
@permission_classes([])
def register(request):
    if request.user.is_authenticated:
        return Response("You must log out first.", status.HTTP_400_BAD_REQUEST)
    
    form = RegisterNewUser(request.data)
    if not form.is_valid():
        return Response(form.errors.as_json(), status.HTTP_400_BAD_REQUEST)
    
    email = form.cleaned_data['email']
    password1 = form.cleaned_data['password1']
    password2 = form.cleaned_data['password2']

    User = get_user_model()
    if User.objects.filter(email=email).exists():
        existing_user =  User.objects.filter(email=email).first()
        # If user exists but hasn't been activated, resend an activation link.
        if not existing_user.is_active:
            activate_user_token = utils.get_account_activation_token(existing_user.userprofile.slug)
            email_lib.send_account_activation_email(existing_user, activate_user_token)
        return Response("This email is already in use.", status.HTTP_400_BAD_REQUEST)
    

    if password1 != password2:
        return Response("Passwords do not match.", status.HTTP_400_BAD_REQUEST)
    try:
        validate_password(password1)
    except ValidationError:
        return Response("Invalid Password.", status.HTTP_400_BAD_REQUEST)
    
    new_user = User.objects.create_user(email, email=email, password=password1)
    try:
        validate_password(password1, user=new_user)
    except ValidationError:
        new_user.delete()
        return Response("Invalid Password.", status.HTTP_400_BAD_REQUEST)

    new_user.is_active = False
    new_user.save(update_fields=['is_active'])
    userprofile = UserProfile.objects.create(user=new_user)

    activate_user_token = utils.get_account_activation_token(userprofile.slug)
    email_lib.send_account_activation_email(new_user, activate_user_token)

    return Response("User Created.", status.HTTP_201_CREATED)


def activate_new_account(request, slug):
    token = request.GET.get("token")
    if not token:
        return HttpResponseBadRequest("Missing Token")
    
    try:
        slug_from_token = get_slug_from_account_activation_token(token)
    except Exception:
        return HttpResponseBadRequest("Invalid Token Format")
    if slug_from_token != slug:
       return HttpResponseBadRequest("Invalid Token Data")

    userprofile = get_object_or_404(UserProfile, slug=slug, user__is_active=False)
    user = userprofile.user
    user.is_active = True
    user.save(update_fields=['is_active'])

    login(request, user)
    return redirect('app-landing')


@login_required
def logout_user(request):
    logout(request)
    return redirect("anon-landing")


def password_reset_email_sent(request):
    return render(request, 'password_reset/anon_password_reset_email_sent.html', {})

def handler404(request, *args, **argv):
    return render(request, "404.html", {})
