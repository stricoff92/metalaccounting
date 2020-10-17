from django.urls import path

from docs import views

urlpatterns = [
    path("", views.documentation_homepage, name="docs-home"),
    path("company-importing-exporting/", views.company_export, name="docs-company-export"),
    path("account-tags/", views.account_tags, name="docs-account-tags"),
    path("assets/", views.assets, name="docs-assets"),
    path("liabilities/", views.liabilities, name="docs-liabilites"),
    path("equity/", views.equity, name="docs-equity"),
    path("revenue/", views.revenue, name="docs-revenue"),
    path("expense/", views.expense, name="docs-expense"),
    path("balance-sheet/", views.balance_sheet, name="docs-balance-sheet"),
    path("income-statement/", views.income_statement, name="docs-income-statement"),
    path("cash-flow-statement/", views.cash_flow_statement, name="docs-cash-flow-statement"),
    path("trial-balance/", views.trial_balance, name="docs-trial-balance"),
    path("entry-types/", views.entry_types, name="docs-entry-types"),
    path("quick-start-guide/", views.quickstart_guide, name="docs-quick-start-guide"),
    path(
        "statement-of-retained-earnings/",
        views.statement_of_retained_earnings,
        name="docs-statement-of-retained-earnings"),
]
