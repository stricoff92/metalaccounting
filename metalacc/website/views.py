
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from api.models import Company
from website.forms import LoginForm


def anon_landing(request):
    if request.user.is_authenticated:
        return redirect("app-landing")
    return render(request, "anon_landing.html", {})


@login_required
def app_landing(request):
    return render(request, "app_landing.html", {'skip_moment_import':True})


@login_required
def app_company(request, slug):
    company = get_object_or_404(Company, user=request.user, slug=slug)
    return render(request, "app_company.html", {'company':company})


@login_required
def app_profile(request):
    return render(request, "app_profile.html", {'skip_moment_import':True})


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
