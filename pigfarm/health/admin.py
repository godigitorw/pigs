from django.contrib import admin
from .models import *


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ('health_target_type', 'sow', 'piglet', 'health_issue', 'treatment_given', 'cost', 'treatment_date', 'status', 'note')
    list_filter = ('health_target_type', 'status')
    search_fields = ('health_issue', 'treatment_given', 'sow__name', 'piglet__name')
    date_hierarchy = 'treatment_date'


@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_days', 'date_added')
    search_fields = ('name',)

@admin.register(VaccinationRecord)
class VaccinationRecordAdmin(admin.ModelAdmin):
    list_display = ('vaccine', 'vaccination_target_type', 'sow', 'piglet', 'vaccination_date', 'next_vaccination_date', 'status')
    list_filter = ('status', 'vaccination_target_type', 'vaccine')
    search_fields = ('sow__name', 'piglet__name', 'vaccine__name')
    ordering = ('-vaccination_date',)

@admin.register(WeightRecord)
class WeightRecordAdmin(admin.ModelAdmin):
    list_display = ('target_type', 'sow', 'piglet', 'recorded_date', 'weight', 'difference', 'status')
    list_filter = ('target_type', 'status')
    search_fields = ('sow__name', 'piglet__name')