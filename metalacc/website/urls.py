from django.urls import path

from website import views


urlpatterns = [
    path('', views.anon_landing, name="anon-landing"),
    path('app/', views.app_main_menu, name="app-main-menu"),
    path('app/company/', views.app_landing, name="app-landing"),
    path('app/company/<slug:slug>/', views.app_company, name="app-company"),
    path('app/company/<slug:slug>/account/', views.app_company_accounts, name="app-accounts"),
    path('app/company/<slug:slug>/default-account/', views.app_company_add_default_accounts, name="app-default-accounts"),
    path('app/account/<slug:slug>/', views.app_account_details, name="app-account-details"),
    path('app/profile/', views.app_profile, name="app-profile"),
    path('login/', views.login_user, name="login"),
    path('logout/', views.logout_user, name="logout"),
    path('register/', views.register, name="register"),
]
