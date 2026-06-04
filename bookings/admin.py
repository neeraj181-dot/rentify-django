from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'renter', 'product', 'start_date', 'end_date', 'total_days', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('renter__username', 'product__title')
    list_editable = ('status',)
    readonly_fields = ('rental_cost', 'total_amount', 'total_days', 'created_at', 'updated_at')
    fieldsets = (
        ('Parties', {'fields': ('renter', 'product')}),
        ('Dates', {'fields': ('start_date', 'end_date', 'total_days')}),
        ('Financials', {'fields': ('price_per_day', 'rental_cost', 'security_deposit', 'total_amount')}),
        ('Status & Notes', {'fields': ('status', 'renter_note', 'owner_note')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
