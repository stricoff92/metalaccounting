
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from api.models import Company, Account, JournalEntryLine
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
        "id", "slug", "number", "name", "type", 
        "is_current", "is_contra", "is_operating","tag")
    accounts = list(Account.objects
        .filter(company=company)
        .order_by("number")
        .values(*account_fields))

    account_ids = [a['id'] for a in accounts]
    account_ids_with_entries = set(JournalEntryLine.objects
        .filter(account_id__in=account_ids)
        .values_list("account_id", flat=True))
    
    for ix, account in enumerate(accounts):
        # Add has_entries field
        accounts[ix]['has_entries'] = account['id'] in account_ids_with_entries

        # Remove id field
        accounts[ix] = {
            k:v for k,v in account.items() if k != "id"}
        
        if account['tag']:
            accounts[ix]['tag'] = Account.ACCOUNT_TAG_NAME_DICT[account['tag']]
    
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

    # Check for duplicate name/number combinations.
    duplicate_account_names = Account.objects.filter(
        name=form.cleaned_data['name'], company=company)
    if duplicate_account_names.exists():
        return Response('An account with that name already exists', status.HTTP_409_CONFLICT)

    duplicate_account_number = Account.objects.filter(
        number=form.cleaned_data['number'], company=company)
    if duplicate_account_number.exists():
        return Response('An account with that number already exists', status.HTTP_409_CONFLICT)
    

    # Verify non null is_current value is appropriate
    is_current = form.cleaned_data.get('is_current')
    account_type = form.cleaned_data.get('type')
    if account_type in Account.CURRENT_TYPES:
        if is_current is None:
            return Response(
                f"is_current cannot be null for type {account_type}",
                status.HTTP_400_BAD_REQUEST)
    else:
        if not is_current is None:
            return Response(
                f"is_current must be null for type {account_type}",
                status.HTTP_400_BAD_REQUEST)

    # Verify non null is_operating value is appropriate
    is_operating = form.cleaned_data.get('is_operating')
    if account_type in Account.OPERATING_TYPES:
        if is_operating is None:
            return Response(
                f"is_operating cannot be null for type {account_type}",
                status.HTTP_400_BAD_REQUEST)
    else:
        if not is_operating is None:
            return Response(
                f"is_operating must be null for type {account_type}",
                status.HTTP_400_BAD_REQUEST)


    account = form.save(commit=False)
    account.company = company
    account.user = request.user
    try:
        account.save()
    except ValidationError as e:
        return Response(e, status.HTTP_400_BAD_REQUEST)

    data = {
        'name':account.name,
        'slug':account.slug,
        'number':account.number,
        'type':account.type,
        'is_contra':account.is_contra,
        'is_current':account.is_current,
        'tag':account.tag,
    }
    return Response(data, status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account_add_default_accounts(request):
    form = CompanySelectionForm(request.data)
    if not form.is_valid():
        return Response(form.errors.as_json())
    company = form.cleaned_data['company']
    if company.user != request.user:
        return Response("company not found", status.HTTP_404_NOT_FOUND)

    if company.account_set.exists():
        return Response(
            "this company already has accounts associated",
            status.HTTP_400_BAD_REQUEST)
    
    Account.objects.create_default_accounts(company)
    return Response({}, status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account_edit(request, slug):
    account = get_object_or_404(Account, slug=slug, user=request.user)
    account_type = account.type
    company = account.company

    form = EditAccountForm(request.data, instance=account)
    if not form.is_valid():
        return Response(form.errors.as_json(), status.HTTP_400_BAD_REQUEST)
    
    # Check for duplicate name/number combinations.
    duplicate_account_names = Account.objects.exclude(id=account.id).filter(
        name=form.cleaned_data['name'], company=company)
    if duplicate_account_names.exists():
        return Response('An account with that name already exists', status.HTTP_409_CONFLICT)

    duplicate_account_number = Account.objects.exclude(id=account.id).filter(
        number=form.cleaned_data['number'], company=company)
    if duplicate_account_number.exists():
        return Response('An account with that number already exists', status.HTTP_409_CONFLICT)


    # Verify non null is_current value is appropriate
    is_current = form.cleaned_data.get('is_current')
    if account.supports_is_current:
        if is_current is None:
            return Response(
                f"is_current cannot be null for type {account_type}",
                status.HTTP_400_BAD_REQUEST)
    else:
        if is_current is not None:
            return Response(
                f"is_current must be null for type {account_type}",
                status.HTTP_400_BAD_REQUEST)


    # Verify non null is_operating value is appropriate
    is_operating = form.cleaned_data.get('is_operating')
    if account.supports_is_operating:
        if is_operating is None:
            return Response(
                f"is_operating cannot be null for type {account_type}",
                status.HTTP_400_BAD_REQUEST)
    else:
        if not is_operating is None:
            return Response(
                f"is_operating must be null for type {account_type}",
                status.HTTP_400_BAD_REQUEST)


    try:
        account = form.save()
    except ValidationError as e:
        return Response(e, status.HTTP_400_BAD_REQUEST)
    
    data = {
        'slug':account.slug,
        'name':account.name,
        'number':account.number,
        'type':account.type,
        'is_contra':account.is_contra,
        'is_current':account.is_current,
        'tag':account.tag,
    }
    return Response(data, status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account_delete(request, slug):
    account = get_object_or_404(Account, slug=slug, user=request.user)
    if account.journalentryline_set.exists():
        return Response(
            "Cannot Delete. This account is referenced by a journal entry.",
            status.HTTP_400_BAD_REQUEST)
    account.delete()
    return Response({}, status.HTTP_204_NO_CONTENT)
