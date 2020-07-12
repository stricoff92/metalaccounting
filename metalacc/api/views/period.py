
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from api.models import Company, Period
from api.forms.company import CompanySelectionForm
from api.forms.period import PeriodForm


def _get_date_conflict_Q(start, end):
    return (
        Q(start__lte=start, end__gte=start)
        | Q(start__gte=start, start__lte=end)
        | Q(start__gte=start, end__lte=end)
        | Q(start__lte=start, end__gte=end))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def period_new(request):

    # Validate forms.
    company_form = CompanySelectionForm(request.data)
    if not company_form.is_valid():
        return Response(company_form.errors.as_json(), status.HTTP_400_BAD_REQUEST)
    company = company_form.cleaned_data['company']
    if company.user != request.user:
        return Response("company not found", status.HTTP_404_NOT_FOUND)
    
    period_count = company.period_set.count()
    max_periods_per_company = request.user.userprofile.object_limit_periods_per_company
    if period_count >= max_periods_per_company:
        return Response(
            "cannot add additional periods to this company",
            status.HTTP_400_BAD_REQUEST)

    period_form = PeriodForm(request.data)
    if not period_form.is_valid():
        return Response(period_form.errors.as_json(), status.HTTP_400_NOT_FOUND)
    
    period = period_form.save(commit=False)
    period.company = company

    # Verify the period's start/end does not conflict.
    conflicting_periods = Period.objects.filter(
        Q(company=company)
        & _get_date_conflict_Q(period.start, period.end))
    if conflicting_periods.exists():
        return Response('start/end conflict', status.HTTP_400_BAD_REQUEST)
    
    # Save to the database.
    period.save()
    data = {
        'start':period.start,
        'end':period.end,
        'slug':period.slug,
    }
    return Response(data, status.HTTP_201_CREATED)
