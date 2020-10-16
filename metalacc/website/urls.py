from django.urls import path
from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.views.decorators.http import require_POST

from website import views


urlpatterns = [
    path('', views.anon_landing, name="anon-landing"),
    path('app/', views.app_main_menu, name="app-main-menu"),

    path('app/export-tools/', views.app_export_tools_menu, name="app-export-tools-menu"),

    path('app/company/', views.app_landing, name="app-landing"),
    path('app/company/import/', views.app_import_company, name="app-company-import"),
    path('app/company/<slug:slug>/', views.app_company, name="app-company"),
    path('app/company/<slug:slug>/export/', views.app_export_company, name="app-company-export"),
    path('app/company/<slug:slug>/period/', views.app_periods, name="app-period"),
    path('app/company/<slug:slug>/account/', views.app_company_accounts, name="app-accounts"),
    path('app/company/<slug:slug>/account/csv/', views.app_company_accounts_csv, name="app-accounts-csv"),
    path('app/company/<slug:slug>/default-account/', views.app_company_add_default_accounts, name="app-default-accounts"),
    path('app/account/<slug:slug>/', views.app_account_details, name="app-account-details"),
    path('app/period/<slug:slug>/', views.app_period_detail, name="app-period-details"),
    path("app/period/<slug:slug>/je/csv/", views.app_period_je_csv, name="app-period-je-csv"),

    path('app/journal_entry/<slug:slug>/', views.app_jounral_entry_detail, name="app-journal-entry-details"),

    path('app/period/<slug:period_slug>/taccount/<slug:account_slug>/', views.t_account, name="app-t-account"),
    path('app/period/<slug:period_slug>/taccount/csv/<slug:account_slug>/', views.t_account_csv, name="app-t-account-csv"),

    path('app/period/<slug:slug>/trial-balance/', views.trial_balance, name="app-trial-balance"),
    path('app/period/<slug:slug>/trial-balance/csv/', views.trial_balance_csv, name="app-trial-balance-csv"),
    path('app/period/<slug:slug>/income-statement/', views.income_statement, name="app-income-statement"),
    path('app/period/<slug:slug>/balance-sheet/', views.balance_sheet, name="app-balance-sheet"),
    path('app/period/<slug:slug>/statement-of-retained-earnings/', views.retained_earnings, name="app-retained-earnings"),
    path('app/period/<slug:slug>/statement-of-cash-flows/worksheet/', views.statement_of_cash_flows_worksheet, name="app-cash-flow-worksheet"),
    path('app/period/<slug:slug>/statement-of-cash-flows/', views.statement_of_cash_flows, name="app-cash-flow"),
    
    path('app/profile/', views.app_profile, name="app-profile"),
    path('login/', views.login_user, name="login"),
    path('logout/', views.logout_user, name="logout"),
    path('register/', views.register, name="register"),

    # Send Password Email
    path('reset-password-send-email/',
        require_POST(auth_views.PasswordResetView.as_view(
            email_template_name="password_reset/email/password_reset.email"
        )),
        name='password_reset_send_email',
    ),

    # Password reset link sent confirmation
    path('reset-password/done/', views.password_reset_email_sent, name='password_reset_done'),

    # Enter new password page
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(template_name="password_reset/confirm_new_password.html"),
        name='password_reset_confirm',
    ),

    # New password saved page
    path('reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(template_name="password_reset/complete.html"),
        name='password_reset_complete',
    ),


]
