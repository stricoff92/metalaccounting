
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from api.models import Company
from api.forms.company import (
    CompanyForm,
    ImportCompanyForm,
    CompareCompanyDataForm,
    CompareCompanySettingsForm
)
from api.lib import company_export
from api.lib.grader import Grader


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_import(request):
    # Check object limit.
    if request.user.userprofile.at_company_object_limit:
        return Response(
            "user cannot add additional companies",
            status.HTTP_400_BAD_REQUEST)

    form = ImportCompanyForm(request.data)
    if not form.is_valid():
        return Response("Invalid data.", status.HTTP_400_BAD_REQUEST)
    
    new_company = company_export.import_company_data(
        form.cleaned_data['decoded_data'], request.user)

    data = {
        'slug':new_company.slug,
        'name':new_company.name,
    }
    return Response(data, status.HTTP_201_CREATED)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account_data_export_history(request):
    form = ImportCompanyForm(request.data)
    if not form.is_valid():
        return Response("Invalid data.", status.HTTP_400_BAD_REQUEST)
        
    user_history = form.cleaned_data['decoded_data']['meta']['user_history']
    user_history.sort(key=lambda r: int(r['timestamp']))
    return Response(user_history, status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_list(request):
    companies = (Company.objects
        .filter(user=request.user)
        .order_by("name")
        .values("name", "slug"))
    return Response(companies, status.HTTP_200_OK) 


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_new(request):
    if request.user.userprofile.at_company_object_limit:
        return Response(
            "user cannot add additional companies",
            status.HTTP_400_BAD_REQUEST)

    form = CompanyForm(request.data)
    if not form.is_valid():
        return Response(form.errors, status.HTTP_400_BAD_REQUEST)
    
    new_company_name = form.cleaned_data['name']
    if Company.objects.filter(user=request.user, name=new_company_name).exists():
        return Response(
            "a company with that name already exists",
            status.HTTP_400_BAD_REQUEST) 

    company = form.save(commit=False)
    company.user = request.user
    company.save()

    data = {
        'slug':company.slug,
        'name':company.name,
    }
    return Response(data, status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_edit(request, slug):
    company = get_object_or_404(Company, slug=slug, user=request.user)
    form = CompanyForm(request.data, instance=company)
    if not form.is_valid():
        return Response(form.errors, status.HTTP_400_BAD_REQUEST)
    
    company_name = form.cleaned_data['name']
    if Company.objects.filter(user=request.user, name=company_name).exclude(id=company.id).exists():
        return Response(
            "a company with that name already exists",
            status.HTTP_400_BAD_REQUEST) 

    company = form.save()
    data = {
        'slug':company.slug,
        'name':company.name,
    }
    return Response(data, status.HTTP_200_OK)   


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_delete(request, slug):
    company = get_object_or_404(Company, slug=slug, user=request.user)
    company.delete()
    return Response({}, status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_compare(request):
    print("request.data", request.data)

    form = CompareCompanyDataForm(request.data)
    if not form.is_valid():
        return Response(form.errors, status.HTTP_400_BAD_REQUEST)
    
    settings_form = CompareCompanySettingsForm(request.data)
    if not settings_form.is_valid():
        return Response(settings_form.errors, status.HTTP_400_BAD_REQUEST)

    grader = Grader(
        form.cleaned_data['decoded_test_company_text_data'],
        form.cleaned_data['decoded_control_company_text_data'],
        **settings_form.cleaned_data)
    
    diff_text = grader.generate_git_diff()
    diff_rows = diff_text.split("\n")
    diff_rows = diff_rows[4:]

    data = {
        'diff_rows':diff_rows,
        'test_user_hash':form.cleaned_data['decoded_test_company_text_data']['meta']['user_history'][0]['user_hash'],
        'control_user_hash':form.cleaned_data['decoded_control_company_text_data']['meta']['user_history'][0]['user_hash'],
    }

    return Response(data, status.HTTP_200_OK)
