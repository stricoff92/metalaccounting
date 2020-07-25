
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from website.forms import LoginForm

def anon_landing(request):
    if request.user.is_authenticated:
        return redirect("app-landing")
    return render(request, "anon_landing.html", {})


@login_required
def app_landing(request):
    return render(request, "app_landing.html", {})


def login_user(request):
    if request.method == 'GET':
        return redirect("anon-landing")

    if request.user.is_authenticated:
        raise NotImplementedError()

    form = LoginForm(request.POST)
    if not form.is_valid():
        data = {
            "loginerror":"invalid email/password",
        }
        return render(request, 'anon_landing.html', data)
    
    user = authenticate(
        request, 
        username=form.cleaned_data['email'], 
        password=form.cleaned_data['password'])

    if user is not None:
        login(request, user)
        return redirect('app-landing')
    else:
        data = {
            "loginerror":"invalid email/password",
            "loginemail":form.cleaned_data['email'],
        }
        return render(request, 'anon_landing.html', data)


@require_POST
def register(request):
    if request.user.is_authenticated:
        raise NotImplementedError()


@login_required
def logout_user(request):
    logout(request)
    return redirect("anon-landing")
