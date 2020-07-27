from django.urls import path

from website import views


urlpatterns = [
    path('', views.anon_landing, name="anon-landing"),
    path('app/', views.app_main_menu, name="app-main-menu"),
    path('app/company/', views.app_landing, name="app-landing"),
    path('app/company/<slug:slug>/', views.app_company, name="app-company"),
    path('app/profile/', views.app_profile, name="app-profile"),
    path('login/', views.login_user, name="login"),
    path('logout/', views.logout_user, name="logout"),
    path('register/', views.register, name="register"),
]
