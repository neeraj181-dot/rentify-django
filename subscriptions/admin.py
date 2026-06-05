from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, PaymentRecord, AddressAccessRequest, DailyMessageCount


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'billing_cycle', 'price', 'currency', 'is_active', 'display_order')
    list_filter = ('is_active', 'is_featured', 'billing_cycle')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'price')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'status', 'started_at', 'expires_at', 'auto_renew')
    list_filter = ('status', 'auto_renew', 'created_at')
    search_fields = ('user__username', 'user__email', 'plan__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('User & Plan', {
            'fields': ('id', 'user', 'plan')
        }),
        ('Status', {
            'fields': ('status', 'started_at', 'expires_at', 'cancelled_at', 'auto_renew')
        }),
        ('Payment', {
            'fields': ('payment_gateway', 'gateway_sub_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'currency', 'status', 'gateway', 'created_at')
    list_filter = ('status', 'gateway', 'created_at')
    search_fields = ('user__username', 'user__email', 'gateway_order_id', 'gateway_payment_id')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        ('User & Plan', {
            'fields': ('id', 'user', 'plan', 'subscription')
        }),
        ('Amount', {
            'fields': ('amount', 'currency')
        }),
        ('Payment Status', {
            'fields': ('status', 'failure_reason')
        }),
        ('Gateway Details', {
            'fields': ('gateway', 'gateway_order_id', 'gateway_payment_id', 'gateway_signature')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AddressAccessRequest)
class AddressAccessRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'owner', 'listing', 'status', 'requested_at', 'responded_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('requester__username', 'requester__email', 'listing__title', 'owner__username')
    readonly_fields = ('requested_at', 'responded_at')
    fieldsets = (
        ('Request Details', {
            'fields': ('requester', 'owner', 'listing', 'status')
        }),
        ('Response', {
            'fields': ('owner_note', 'requested_at', 'responded_at')
        }),
    )


@admin.register(DailyMessageCount)
class DailyMessageCountAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'count')
    list_filter = ('date', 'user')
    search_fields = ('user__username', 'user__email')
    date_hierarchy = 'date'
