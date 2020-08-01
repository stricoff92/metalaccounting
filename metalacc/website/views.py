
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.http import HttpResponseNotAllowed

from api.models import Company, Account, Period, JournalEntry
from api.models.account import DEFAULT_ACCOUNTS
from website.forms import LoginForm


def anon_landing(request):
    if request.user.is_authenticated:
        return redirect("app-landing")
    return render(request, "anon_landing.html", {})


@login_required
def app_main_menu(request):
    data = {
        'skip_moment_import':True,
    }
    return render(request, "app_main_menu.html", data)


@login_required
def app_landing(request):
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
        'company':company,
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
    }
    return render(request, "app_company_accounts.html", data)


@login_required
def app_account_details(request, slug):
    account = get_object_or_404(
        Account, company__user=request.user, slug=slug)
    company = account.company

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
        'account':account,
        'breadcrumbs':breadcrumbs,
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
            'number':a[3],
            'name':a[4],
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
