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
    ], key=lambda item: item['name'].lower())

    return render(request, "docs_root.html", {'index_items':index_items})


def assets(request):
    return render(request, "assets.html", {})

def liabilities(request):
    return render(request, "liabilities.html", {})

def equity(request):
    return render(request, "equity.html", {})

def revenue(request):
    return render(request, "revenue.html", {})

def expense(request):
    return render(request, "expense.html", {})

def balance_sheet(request):
    return render(request, "balance_sheet.html", {})

def income_statement(request):
    return render(request, "income_statement.html", {})

def cash_flow_statement(request):
    return render(request, "cash_flow_statement.html", {})

def statement_of_retained_earnings(request):
    return render(request, "statement_of_retained_earnings.html", {})

def trial_balance(request):
    return render(request, "trial_balance.html", {})

def account_tags(request):
    return render(request, "account_tags.html", {})

def company_export(request):
    return render(request, "company_export.html", {})
