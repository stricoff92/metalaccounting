
from collections import defaultdict

from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from api.models import Company, Period, JournalEntry, Account
from api.forms.company import CompanySelectionForm
from api.forms.period import PeriodForm, CashFlowWorkSheetRowForm
from api.utils import is_valid_slug, get_date_conflict_Q



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def period_list(request):
    company_slug = request.query_params.get('company')
    if not company_slug:
        return Response(
            "company param required", status.HTTP_400_BAD_REQUEST)
    if not is_valid_slug(company_slug):
        return Response(
            "invalid company slug", status.HTTP_400_BAD_REQUEST)

    company = get_object_or_404(Company, user=request.user, slug=company_slug)
    periods = list(Period.objects
        .filter(company=company)
        .order_by("start")
        .values("id", "slug", "start", "end"))

    # Aggregate journal entry info by period
    period_ids = [p['id'] for p in periods]
    journal_entries = (JournalEntry.objects
        .filter(period_id__in=period_ids)
        .values('period_id', 'is_adjusting_entry', 'is_closing_entry'))
    je_data_by_period = defaultdict(lambda : {
        'journal_entry_count':0,
        'has_closing_entries':False,
        'has_adjusting_entries':False,
    })
    for je in journal_entries:
        period_id = je['period_id']
        je_data_by_period[period_id]['journal_entry_count'] += 1
        if je['is_closing_entry']:
            je_data_by_period[period_id]['has_closing_entries'] = True
        if je['is_adjusting_entry']:
            je_data_by_period[period_id]['has_adjusting_entries'] = True
    
    # Enrich period data with journal entry into
    for ix, period in enumerate(periods):
        period_id = period['id']
        periods[ix]['journal_entry_count'] = je_data_by_period[period_id]['journal_entry_count']
        periods[ix]['has_closing_entries'] = je_data_by_period[period_id]['has_closing_entries']
        periods[ix]['has_adjusting_entries'] = je_data_by_period[period_id]['has_adjusting_entries']
        periods[ix] = {k:v for k,v in periods[ix].items() if k != 'id'} # remove id

    return Response(periods, status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def period_new(request):

    # Validate forms.
    company_form = CompanySelectionForm(request.data)
    if not company_form.is_valid():
        return Response(
            company_form.errors.as_json(), status.HTTP_400_BAD_REQUEST)
    company = company_form.cleaned_data['company']
    if company.user != request.user:
        return Response(
            "company not found", status.HTTP_404_NOT_FOUND)
    
    period_count = company.period_set.count()
    max_periods_per_company = request.user.userprofile.object_limit_periods_per_company
    if period_count >= max_periods_per_company:
        return Response(
            "cannot add additional periods to this company",
            status.HTTP_400_BAD_REQUEST)

    period_form = PeriodForm(request.data)
    if not period_form.is_valid():
        return Response(
            period_form.errors.as_json(),
            status.HTTP_400_BAD_REQUEST)
    
    period_start = period_form.cleaned_data['start']
    period_end = period_form.cleaned_data['end']

    # Verify the period's start/end does not conflict.
    conflicting_periods = Period.objects.filter(
        Q(company=company)
        & get_date_conflict_Q(period_start, period_end))
    if conflicting_periods.exists():
        return Response(
            'start and end date overlaps with another period',
            status.HTTP_409_CONFLICT)
    
    # Save to the database.
    period = period_form.save(commit=False)
    period.company = company
    period.save()
    data = {
        'start':period.start,
        'end':period.end,
        'slug':period.slug,
    }
    return Response(data, status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def period_edit(request, slug):

    period = get_object_or_404(Period, slug=slug, company__user=request.user)
    company = period.company
    form = PeriodForm(request.data, instance=period)
    if not form.is_valid():
        return Response(form.errors.as_json(), status.HTTP_400_BAD_REQUEST)

    new_start = form.cleaned_data['start']
    new_end = form.cleaned_data['end']

    # Check that no journal entries exist outside the new start/end
    je_conflicts = JournalEntry.objects.filter(
        Q(period=period)
        & (Q(date__gt=new_end) | Q(date__lt=new_start)))
    if je_conflicts.exists():
        return Response(
            "Journal Entry exists outside start/end",
            status.HTTP_400_BAD_REQUEST)

    # Verify the period's start/end does not conflict.
    conflicting_periods = Period.objects.filter(
        Q(company=company)
        & get_date_conflict_Q(new_start, new_end))
    if conflicting_periods.exclude(id=period.id).exists():
        return Response('start and end date overlaps with another period', status.HTTP_409_CONFLICT)
    
    period = form.save()
    data = {
        'start':period.start,
        'end':period.end,
        'slug':period.slug,
    }
    return Response(data, status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def period_delete(request, slug):
    period = get_object_or_404(Period, slug=slug, company__user=request.user)
    period.delete()
    return Response({}, status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def period_reset_cashflow_worksheet(request, slug):
    period = get_object_or_404(Period, slug=slug, company__user=request.user)
    try:
        cash_flow_worksheet = period.cashflowworksheet
    except ObjectDoesNotExist:
        return Response({}, status.HTTP_400_BAD_REQUEST)

    cash_flow_worksheet.delete()
    return Response({}, status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_cashflow_worksheet(request, slug):
    period = get_object_or_404(Period, slug=slug, company__user=request.user)
    company = period.company
    try:
        cash_flow_worksheet = period.cashflowworksheet
    except ObjectDoesNotExist:
        pass
    else:
        return Response({}, status.HTTP_409_CONFLICT)
    
    if not company.account_set.filter(tag=Account.TAG_CASH).exists():
        return Response("Account with Cash tag is required.", status.HTTP_400_BAD_REQUEST)
    
    if not isinstance(request.data, list):
        return Response({}, status.HTTP_400_BAD_REQUEST)

    # Parse request body
    encountered_slugs = set()
    form_data = []
    for row in request.data:
        row_form = CashFlowWorkSheetRowForm(request.data)
        if not row_form.is_valid():
            return Response(row_form.errors, status.HTTP_400_BAD_REQUEST)
        
        if row_form.cleaned_data['journal_entry_slug'] in encountered_slugs:
            return Response({}, status.HTTP_400_BAD_REQUEST)
        else:
            encountered_slugs.add(row_form.cleaned_data['journal_entry_slug'])
        
        journal_entry = get_object_or_404(
            JournalEntry, 
            slug=row_form.cleaned_data['journal_entry_slug'],
            period=period)

        form_data.append({
            'journal_entry':journal_entry,
            'operations':row_form.cleaned_data['operations'],
            'investments':row_form.cleaned_data['investments'],
            'finances':row_form.cleaned_data['finances'],
        })