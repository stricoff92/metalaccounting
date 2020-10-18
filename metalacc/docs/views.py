from django.shortcuts import render
from django.urls import reverse


def documentation_homepage(request):
    index_items = sorted([
        {"name":"Asset", "href":reverse("docs-assets")},
        {"name":"Liability", "href":reverse("docs-liabilites")},
        {"name":"Equity", "href":reverse("docs-equity")},
        {"name":"Revenue", "href":reverse("docs-revenue")},
        {"name":"Expense", "href":reverse("docs-expense")},
        {"name":"Balance Sheet", "href":reverse("docs-balance-sheet")},
        {"name":"Income Statement", "href":reverse("docs-income-statement")},
        {"name":"Cash Flow Statement", "href":reverse("docs-cash-flow-statement")},
        {"name":"Retained Earnings Statement", "href":reverse("docs-statement-of-retained-earnings")},
        {"name":"Trial Balance", "href":reverse("docs-trial-balance")},
        {"name":"Account Tags", "href":reverse("docs-account-tags")},
        {"name":"Import and Export Company Snapshots", "href":reverse("docs-company-export")},
        {"name":"Entry Types", "href":reverse("docs-entry-types")},
    ], key=lambda item: item['name'].lower())
    breadcrumbs = [{
        "value":"Docs",
    }]
    if request.user.is_authenticated:
        breadcrumbs.insert(0, {
            'value':'Main Menu',
            'href':reverse("app-main-menu"),
        })
    return render(request, "docs_root.html", {'index_items':index_items, 'breadcrumbs':breadcrumbs})


def assets(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Asset",
    }]
    return render(request, "assets.html", {'breadcrumbs':breadcrumbs})

def liabilities(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Liability",
    }]
    return render(request, "liabilities.html", {'breadcrumbs':breadcrumbs})

def equity(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Equity",
    }]
    return render(request, "equity.html", {'breadcrumbs':breadcrumbs})

def revenue(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Revenue",
    }]
    return render(request, "revenue.html", {'breadcrumbs':breadcrumbs})

def expense(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Expense",
    }]
    return render(request, "expense.html", {'breadcrumbs':breadcrumbs})

def balance_sheet(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Balance Sheet",
    }]
    return render(request, "balance_sheet.html", {'breadcrumbs':breadcrumbs})

def income_statement(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Income Statement",
    }]
    return render(request, "income_statement.html", {'breadcrumbs':breadcrumbs})

def cash_flow_statement(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Cash Flow Statement",
    }]
    return render(request, "cash_flow_statement.html", {'breadcrumbs':breadcrumbs})

def statement_of_retained_earnings(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Statement of Retained Earnings",
    }]
    return render(request, "statement_of_retained_earnings.html", {'breadcrumbs':breadcrumbs})

def trial_balance(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Trial Balance",
    }]
    return render(request, "trial_balance.html", {'breadcrumbs':breadcrumbs})

def account_tags(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Account Tags",
    }]
    return render(request, "account_tags.html", {'breadcrumbs':breadcrumbs})

def company_export(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Snapshots",
    }]
    return render(request, "company_export.html", {'breadcrumbs':breadcrumbs})

def entry_types(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Entry Types",
    }]
    return render(request, "entry_types.html", {'breadcrumbs':breadcrumbs})

def quickstart_guide(request):
    breadcrumbs = [{
        "value":"Docs",
        "href":reverse("docs-home"),
    },{
        "value":"Quickstart Guide",
    }]
    return render(request, "quickstart_guide.html", {'breadcrumbs':breadcrumbs})
