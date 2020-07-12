
from django.conf.urls import url, include
from django.urls import path

from api import views

urlpatterns = [

    # Company Routes
    path('company/list/', views.company_list, name="company-list"),
    path('company/new/', views.company_new, name="company-new"),
    path('company/edit/<slug:slug>/', views.company_edit, name="company-edit"),
    path('company/delete/<slug:slug>/', views.company_delete, name="company-delete"),

    # Period Routes
    path('period/new/', views.period_new, name="period-new"),
    path('period/edit/<slug:slug>/', views.period_edit, name="period-edit"),
    path('period/delete/<slug:slug>/', views.period_delete, name="period-delete"),

]
