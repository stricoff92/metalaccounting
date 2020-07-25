from django.urls import path

from website import views


urlpatterns = [
    path('', views.anon_landing, name="anon-landing"),
    path('app/', views.app_landing, name="app-landing"),
    path('login/', views.login_user, name="login"),
    path('logout/', views.logout_user, name="logout"),
    path('register/', views.register, name="register"),
]
