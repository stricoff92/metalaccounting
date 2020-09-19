
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from api.models import Company
from api.forms.company import CompanyForm, ImportCompanyForm
from api.lib import company_export


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_import(request):

    # Check object limit.
    max_companies = request.user.userprofile.object_limit_companies
    if Company.objects.filter(user=request.user).count() >= max_companies:
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
    # Check object limit.
    max_companies = request.user.userprofile.object_limit_companies
    if Company.objects.filter(user=request.user).count() >= max_companies:
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

