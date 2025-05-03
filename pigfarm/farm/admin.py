# farm/admin.py
from django.contrib import admin
from .models import *
from django.utils.html import format_html

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'pig_count', 'status')
    search_fields = ('name',)
    list_filter = ('status',)


@admin.register(Sow)
class SowAdmin(admin.ModelAdmin):
    list_display = ('name', 'unique_id', 'registered_date', 'birth_count', 'total_piglets', 'category', 'status', 'room')
    search_fields = ('name', 'unique_id')
    list_filter = ('category', 'room')


@admin.register(FeedStock)
class FeedStockAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'feed_type', 'stock_quantity', 'unit',
        'cost_per_unit', 'total_cost', 'stock_status_badge', 'date_added'
    )
    search_fields = ('name', 'feed_type')
    list_filter = ('feed_type', 'unit')
    ordering = ('-date_added',)
    readonly_fields = ('total_cost',)

    def stock_status_badge(self, obj):
        status = obj.stock_status()
        color = 'green' if status == 'Sufficient' else 'red'
        return format_html('<span style="color: white; background-color: {}; padding: 2px 8px; border-radius: 6px;">{}</span>', color, status)
    stock_status_badge.short_description = 'Stock Status'


@admin.register(FeedingRecord)
class FeedingRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'feeding_target_type', 'get_target_name', 'feed', 'quantity_used', 'total_cost', 'recorded_at')
    list_filter = ('feeding_target_type', 'recorded_at')
    search_fields = ('sow__name', 'piglet__name', 'feed__name')
    ordering = ('-recorded_at',)

    def get_target_name(self, obj):
        """Display the name of the sow or piglet being fed"""
        return obj.sow.name if obj.sow else obj.piglet.name if obj.piglet else "Unknown"

    get_target_name.short_description = "Animal"


@admin.register(InactivePig)
class InactivePigAdmin(admin.ModelAdmin):
    list_display = ('name', 'pig_type', 'reason', 'date_marked_inactive')
    list_filter = ('pig_type', 'date_marked_inactive')
    search_fields = ('name', 'reason')



@admin.register(Piglet)
class PigletAdmin(admin.ModelAdmin):
    list_display = ('name', 'sow', 'birth_date', 'initial_weight', 'current_weight', 'status')
    list_filter = ('status', 'sow')
    search_fields = ('name',)



@admin.register(SoldPig)
class SoldPigAdmin(admin.ModelAdmin):
    list_display = ('pig_type', 'sow', 'piglet', 'sold_price', 'total_cost', 'date_sold')
    list_filter = ('pig_type', 'date_sold')
    search_fields = ('sow__name', 'piglet__name')