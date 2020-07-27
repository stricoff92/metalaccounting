
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from api.models import Company, Account
from api.forms.account import NewAccountForm, EditAccountForm
from api.forms.company import CompanySelectionForm
from api.utils import is_valid_slug


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_list(request):
    company_slug = request.query_params.get('company')
    if not company_slug:
        return Response(
            "company param required", status.HTTP_400_BAD_REQUEST)
    if not is_valid_slug(company_slug):
        return Response(
            "invalid company slug", status.HTTP_400_BAD_REQUEST)

    company = get_object_or_404(Company, user=request.user, slug=company_slug)

    account_fields = (
        "slug", "number", "name", "type", 
        "is_current", "is_contra")
    accounts = (Account.objects
        .filter(company=company)
        .order_by("number")
        .values(*account_fields))
    return Response(accounts, status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account_new(request):    
    form = NewAccountForm(request.data)
    if not form.is_valid():
        return Response(form.errors.as_json(), status.HTTP_400_BAD_REQUEST)
    
    comapany_form = CompanySelectionForm(request.data)
    if not comapany_form.is_valid():
        return Response(comapany_form.errors.as_json(), status.HTTP_400_BAD_REQUEST)
    company = comapany_form.cleaned_data['company']
    if company.user != request.user:
        return Response("company not found", status.HTTP_404_NOT_FOUND)

    # Check object limit.
    max_accounts = request.user.userprofile.object_limit_accounts
    if Account.objects.filter(user=request.user, company=company).count() >= max_accounts:
        return Response(
            "user cannot add additional accounts", status.HTTP_400_BAD_REQUEST)

    duplicate_accounts = Account.objects.filter(
        name=form.cleaned_data['name'], number=form.cleaned_data['number'],
        company=company, user=request.user)
    if duplicate_accounts.exists():
        return Response('duplicate account found', status.HTTP_400_BAD_REQUEST)


    account = form.save(commit=False)
    account.company = company
    account.user = request.user
    try:
        account.save()
    except ValidationError as e:
        return Response(e, status.HTTP_400_BAD_REQUEST)

    data = {
        'name':account.name,
        'number':account.number,
        'type':account.type,
        'is_contra':account.is_contra,
        'is_current':account.is_current,
    }
    return Response(data, status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account_edit(request, slug):
    account = get_object_or_404(Account, slug=slug, user=request.user)

    form = EditAccountForm(request.data, instance=account)
    if not form.is_valid():
        return Response(form.errors.as_json(), status.HTTP_400_BAD_REQUEST)
    
    new_name = form.cleaned_data['name']
    new_number = form.cleaned_data['number']
    duplicate_accounts = Account.objects.filter(
        company=account.company, user=request.user,
        number=new_number, name=new_name)
    if duplicate_accounts.exclude(id=account.id).exists():
        return Response('duplicate account found', status.HTTP_400_BAD_REQUEST)

    try:
        account = form.save()
    except ValidationError as e:
        return Response(e, status.HTTP_400_BAD_REQUEST)
    data = {
        'name':account.name,
        'number':account.number,
        'type':account.type,
        'is_contra':account.is_contra,
        'is_current':account.is_current,
    }
    return Response(data, status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account_delete(request, slug):
    account = get_object_or_404(Account, slug=slug, user=request.user)
    account.delete()
    return Response({}, status.HTTP_204_NO_CONTENT)
