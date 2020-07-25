
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
    path('company/new/', views.company_new, name="company-new"),
    path('company/edit/<slug:slug>/', views.company_edit, name="company-edit"),
    path('company/delete/<slug:slug>/', views.company_delete, name="company-delete"),

    # Period Routes
    path('period/new/', views.period_new, name="period-new"),
    path('period/edit/<slug:slug>/', views.period_edit, name="period-edit"),
    path('period/delete/<slug:slug>/', views.period_delete, name="period-delete"),

    # Account Routes
    path('account/new/', views.account_new, name="account-new"),
    path('account/edit/<slug:slug>/', views.account_edit, name="account-edit"),
    path('account/delete/<slug:slug>/', views.account_delete, name="account-delete"),

    # Journal Entry Routes
    path('je/new/', views.journal_entry_new, name="je-new"),
    path('je/delete/<slug:slug>/', views.journal_entry_delete, name="je-delete"),
]
