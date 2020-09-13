
from collections import defaultdict
import json

from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, serializers

from api.models import JournalEntry, JournalEntryLine, Period
from api.forms.journal_entry import NewJournalEntryForm, NewJournalEntryLineForm


# Serializers for these views

class JournalEntryLineSerializer(serializers.ModelSerializer):

    account__name = serializers.SerializerMethodField()
    account__number = serializers.SerializerMethodField()
    account__slug = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntryLine
        fields = (
            "slug",
            "account__name",
            "account__number",
            "account__slug",
            "type",
            "amount",
        )
    
    def get_account__name(self, obj):
        return obj.account.name

    def get_account__number(self, obj):
        return obj.account.number

    def get_account__slug(self, obj):
        return obj.account.slug


class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = ('start', 'end', 'slug',)

class JournalEntrySerializer(serializers.ModelSerializer):

    lines = JournalEntryLineSerializer(many=True)
    period = PeriodSerializer()

    class Meta:
        model = JournalEntry
        fields = (
            "slug",
            "date",
            "period",
            "memo",
            "lines",
            'dr_total',
            'cr_total',
        )

# Function based views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def journal_entry_list(request, slug):
    period = get_object_or_404(Period, slug=slug, company__user=request.user)
    try:
        page = int(request.query_params.get("page", 1))
    except ValueError:
        return Response("invalid page", status.HTTP_400_BAD_REQUEST)

    journal_entry_ids = list(JournalEntry.objects
        .filter(period=period)
        .order_by("-date")
        .values_list("id", flat=True))

    page_size = 50
    start_ix = (page - 1) * page_size
    end_ix = start_ix + page_size
    journal_entry_ids = journal_entry_ids[start_ix:end_ix]
    
    journal_entries = list(JournalEntry.objects
        .filter(id__in=journal_entry_ids)
        .order_by("-date")
        .values("id", "slug", "date", "memo", "is_adjusting_entry", "is_closing_entry"))

    journal_entry_lines = list(JournalEntryLine.objects
        .filter(journal_entry_id__in=journal_entry_ids)
        .values("slug","journal_entry_id", "account__name", "account__number", "account__slug", "type", "amount"))
    
    je_lines_by_je = defaultdict(list)
    for jel in journal_entry_lines:
        je_lines_by_je[jel['journal_entry_id']].append(jel)

    for ix, je in enumerate(journal_entries):
        journal_entry_id = je['id']
        journal_entries[ix]['lines'] = sorted(
            je_lines_by_je[journal_entry_id],
            key=lambda jel: (
                jel['type'] == 'c',
                jel['account__number'],
            )
        )

    return Response(journal_entries, status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def journal_entry_new(request):
    je_form = NewJournalEntryForm(request.data)
    if not je_form.is_valid():
        return Response(
            je_form.errors.as_json(), status.HTTP_400_BAD_REQUEST)
    
    period = je_form.cleaned_data['period']
    company = period.company

    if company.user != request.user:
        return Response(
            {"period":"period not found"} , status.HTTP_404_NOT_FOUND)
    
    entry_date = je_form.cleaned_data['date']
    if not period.start <= entry_date <= period.end:
        return Response(
            {"date":"entry date does not fall within period"},
            status.HTTP_400_BAD_REQUEST)
    
    dr_total = 0
    cr_total = 0
    jel_forms = []
    for entry_post in request.data.get('journal_entry_lines', []):
        jel_form = NewJournalEntryLineForm(entry_post)
        if not jel_form.is_valid():
            return Response(
                jel_form.errors.as_json(), status.HTTP_400_BAD_REQUEST)
        
        # Verify account is owned by this user
        if jel_form.cleaned_data['account'].user != request.user:
            return Response(
                {"account":"account not found"}, status.HTTP_404_NOT_FOUND)

        # Verify the account belongs to the company
        if jel_form.cleaned_data['account'].company != company:
            return Response(
                {"account":"account belongs to another company"}, status.HTTP_400_BAD_REQUEST)

        jel_forms.append(jel_form)

        # Track debit/credit totals
        if jel_form.cleaned_data['type'] == JournalEntryLine.TYPE_DEBIT:
            dr_total += jel_form.cleaned_data['amount']
        elif jel_form.cleaned_data['type'] == JournalEntryLine.TYPE_CREDIT:
            cr_total += jel_form.cleaned_data['amount']
        else:
            raise NotImplementedError()
        
    if not dr_total or not cr_total:
        return Response(
            {"dr/cr balance":"zero changes in balance"}, status.HTTP_400_BAD_REQUEST)  
    if dr_total != cr_total:
        return Response(
            {"dr/cr balance":"debits dont match credits"}, status.HTTP_400_BAD_REQUEST)
    
    je_count = period.journalentry_set.count()
    if je_count >= request.user.userprofile.object_limit_entries_per_period:
        return Response(
            {"object limit":"cannot create additional entries for this period"},
            status.HTTP_400_BAD_REQUEST)


    
    # Save changes to the database
    with transaction.atomic():
        journal_entry = je_form.save()
        for jel_form in jel_forms:
            jel = jel_form.save(commit=False)
            jel.journal_entry = journal_entry
            jel.save()

    data = JournalEntrySerializer(journal_entry).data
    return Response(data, status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def journal_entry_delete(request, slug):
    je = get_object_or_404(
        JournalEntry,
        period__company__user=request.user)
    je.delete()
    return Response({}, status.HTTP_204_NO_CONTENT)
