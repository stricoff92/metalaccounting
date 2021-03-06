
from django.conf.urls import url, include
from django.urls import path
from rest_framework import routers

from api import views

router = routers.DefaultRouter()

# 
router.register(r'userprofile', views.UserProfileViewSet, 'userprofile')

urlpatterns = [
    url(r'^', include(router.urls)),

    # Company Routes
    path('company/list/', views.company_list, name="company-list"),
    path('company/new/', views.company_new, name="company-new"),
    path('company/edit/<slug:slug>/', views.company_edit, name="company-edit"),
    path('company/delete/<slug:slug>/', views.company_delete, name="company-delete"),
    path('company/import/', views.company_import, name="company-import"),
    path('company/compare/', views.company_compare, name="company-compare"),

    path('company/export-history/', views.account_data_export_history, name="company-export-history"),

    # Period Routes
    path('period/list/', views.period_list, name="period-list"),
    path('period/new/', views.period_new, name="period-new"),
    path('period/edit/<slug:slug>/', views.period_edit, name="period-edit"),
    path('period/delete/<slug:slug>/', views.period_delete, name="period-delete"),

    # Cashflow worksheet routes
    path(
        'period/<slug:slug>/reset-cashflow-worksheet/',
        views.period_reset_cashflow_worksheet,
        name="period-reset-cashflow-worksheet"),
    path(
        'period/<slug:slug>/create-cashflow-worksheet/',
        views.create_cashflow_worksheet,
        name="period-create-cashflow-worksheet"),

    # Account Routes
    path('account/list/', views.account_list, name="account-list"),
    path('account/new/', views.account_new, name="account-new"),
    path('account/add-default-accounts/', views.account_add_default_accounts, name="account-add-default-accounts"),
    path('account/edit/<slug:slug>/', views.account_edit, name="account-edit"),
    path('account/delete/<slug:slug>/', views.account_delete, name="account-delete"),

    # Journal Entry Routes
    path('je/new/', views.journal_entry_new, name="je-new"),
    path('je/<slug:slug>/', views.journal_entry_details, name="je-details"),
    path('je/delete/<slug:slug>/', views.journal_entry_delete, name="je-delete"),
    path('period/<slug:slug>/je/list/', views.journal_entry_list, name="je-list"),
]
