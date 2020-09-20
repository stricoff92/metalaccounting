
import random
import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.http import HttpResponseNotAllowed, HttpResponse, HttpResponseBadRequest

from api.models import Company, Account, Period, JournalEntry, JournalEntryLine
from api.models.account import DEFAULT_ACCOUNTS
from api.utils import (
    generate_slug,
    get_report_page_breadcrumbs,
    is_valid_slug
)
from api.lib import reports as reports_lib, company_export
from api import utils
from website.forms import LoginForm


def anon_landing(request):
    if request.user.is_authenticated:
        return redirect("app-landing")
    return render(request, "anon_landing.html", {
        'gallery_image':sorted(utils.get_photo_gallery_images(), key=lambda a: random.random())[0]
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
    except JournalEntry.DoesNotExist:
        last_je = None
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
    data = {
        'period':period,
        'company':company,
        'last_je':last_je,
        'breadcrumbs':breadcrumbs,
    }
    return render(request, "app_period_detail.html", data)


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
    non_operating_expense_accounts = reports_lib.union_account_slugs_across_income_statement_data(
        [current_is_data, previous_is_data], reports_lib.KEY_NON_OPERATING_EXPENSE)
    operating_revenue_accounts = Account.objects.filter(slug__in=operating_revenue_accounts).order_by("number")
    non_operating_revenue_accounts = Account.objects.filter(slug__in=non_operating_revenue_accounts).order_by("number")
    operating_expense_accounts = Account.objects.filter(slug__in=operating_expense_accounts).order_by("number")
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
                previous_is_data[reports_lib.KEY_OPERATING_EXPENSE]['total'] if previous_is_data else None),
            'col3value':(
                current_is_data[reports_lib.KEY_OPERATING_EXPENSE]['total']),
        })

        operating_income_row = {
            'padding':4,
            'border':'border-top',
            'col1value':"Operating Income",
            "col3value": (
                current_is_data[reports_lib.KEY_OPERATING_REVENUE]['total']
                - current_is_data[reports_lib.KEY_OPERATING_EXPENSE]['total']
            )
        }
        if previous_is_data:
            operating_income_row['col2value'] = (
                previous_is_data[reports_lib.KEY_OPERATING_REVENUE]['total']
                - previous_is_data[reports_lib.KEY_OPERATING_EXPENSE]['total']
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
                + current_is_data[reports_lib.KEY_NON_OPERATING_EXPENSE]['total'])
            )
        }
        if previous_is_data:
            net_income_row['col2value'] = (
                (previous_is_data[reports_lib.KEY_OPERATING_REVENUE]['total']
                + previous_is_data[reports_lib.KEY_NON_OPERATING_REVENUE]['total'])
                - (previous_is_data[reports_lib.KEY_OPERATING_EXPENSE]['total']
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

    try:
        cash_flow_worksheet = current_period.cashflowworksheet
    except ObjectDoesNotExist:
        cash_flow_worksheet = None
    worksheet_required = reports_lib.period_requires_cash_flow_worksheet(current_period)

    worksheet_completed = False
    if not worksheet_required:
        worksheet_completed = True
    elif cash_flow_worksheet and cash_flow_worksheet.is_sync:
        worksheet_completed = True


    breadcrumbs = get_report_page_breadcrumbs(current_period, "Cash Flow Worksheet")
    data = {
        'worksheet_completed':worksheet_completed,
        'period':current_period,
        'breadcrumbs':breadcrumbs,
    }
    return render(request, "app_report_cash_flow_worksheet.html", data)



@login_required
def statement_of_cash_flows(request, slug):
    current_period = get_object_or_404(
        Period, company__user=request.user, slug=slug)
    
    # Redirect to the cashflow worksheet if one is required.
    try:
        cash_flow_worksheet = current_period.cashflowworksheet
    except ObjectDoesNotExist:
        cash_flow_worksheet = None
    worksheet_required = reports_lib.period_requires_cash_flow_worksheet(current_period)
    if worksheet_required and (not cash_flow_worksheet or not cash_flow_worksheet.in_sync):
        return redirect("app-cash-flow-worksheet", slug=slug)


    breadcrumbs = get_report_page_breadcrumbs(current_period, "Cash Flow Statement")
    data = {
        'period':current_period,
        'breadcrumbs':breadcrumbs,
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


@require_POST
def register(request):
    if request.user.is_authenticated:
        raise NotImplementedError()


@login_required
def logout_user(request):
    logout(request)
    return redirect("anon-landing")

def handler404(request, *args, **argv):
    return render(request, "404.html", {})
