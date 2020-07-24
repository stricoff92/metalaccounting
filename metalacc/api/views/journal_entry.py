
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

    account_name = serializers.SerializerMethodField()
    account_number = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntryLine
        fields = (
            "slug",
            "account_name",
            "account_number",
            "type",
            "amount",
        )
    
    def get_account_name(self, obj):
        return obj.account.name

    def get_account_number(self, obj):
        return obj.account.number

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
            "period not found", status.HTTP_404_NOT_FOUND)
    
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
                "account not found", status.HTTP_404_NOT_FOUND)

        # Verify the account belongs to the company
        if jel_form.cleaned_data['account'].company != company:
            return Response(
                "account belongs to another company", status.HTTP_400_BAD_REQUEST)

        
        # Verify 

        jel_forms.append(jel_form)

        if jel_form.cleaned_data['type'] == JournalEntryLine.TYPE_DEBIT:
            dr_total += jel_form.cleaned_data['amount']
        elif jel_form.cleaned_data['type'] == JournalEntryLine.TYPE_CREDIT:
            cr_total += jel_form.cleaned_data['amount']
        else:
            raise NotImplementedError()
        
    if not dr_total or not cr_total:
        return Response(
            "zero changes in balance", status.HTTP_400_BAD_REQUEST)  
    if dr_total != cr_total:
        return Response(
            "debits dont match credits", status.HTTP_400_BAD_REQUEST)
    
    period = je_form.cleaned_data['period']
    je_count = period.journalentry_set.count()
    if je_count >= request.user.userprofile.object_limit_entries_per_period:
        return Response(
            "cannot create additional entries for this period",
            status.HTTP_400_BAD_REQUEST)

    if period.user != request.user:
        return Response(
            "period not found", status.HTTP_404_NOT_FOUND) 
    
    with transaction.atomic():
        journal_entry = je_form.save()
        for jel_form in jel_forms:
            jel = jel_form.save(commit=False)
            jel.journal_entry = journal_entry
            jel.save()

    data = JournalEntrySerializer(journal_entry).data
    return Response(data, status.HTTP_201_CREATED)
