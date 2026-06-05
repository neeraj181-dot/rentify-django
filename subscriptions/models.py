from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class SubscriptionPlan(models.Model):
    """Defines available subscription tiers (Monthly, Yearly, etc.)."""
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]

    name        = models.CharField(max_length=100)           # "Premium Monthly"
    slug        = models.SlugField(unique=True)              # "premium-monthly"
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    price       = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    currency    = models.CharField(max_length=3, default='INR')
    duration_days = models.PositiveIntegerField(default=30, help_text='Subscription length in days')
    is_active   = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)        # highlight "Best Value" plan
    display_order = models.PositiveIntegerField(default=0)

    # Feature flags stored on plan level
    unlimited_messages  = models.BooleanField(default=True)
    unlimited_wishlist  = models.BooleanField(default=True)
    view_contact_number = models.BooleanField(default=True)
    view_exact_address  = models.BooleanField(default=True)
    advanced_filters    = models.BooleanField(default=True)
    featured_profile    = models.BooleanField(default=True)
    priority_support    = models.BooleanField(default=True)
    ad_free             = models.BooleanField(default=True)
    early_access        = models.BooleanField(default=True)

    # Free-tier limits (for reference/UI display)
    FREE_MESSAGE_DAILY_LIMIT = 10
    FREE_WISHLIST_LIMIT      = 20

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'price']

    def __str__(self):
        return f"{self.name} — ₹{self.price}/{self.billing_cycle}"

    @property
    def monthly_equivalent(self):
        """Monthly cost — used for yearly plan display."""
        if self.billing_cycle == 'yearly' and self.duration_days >= 365:
            return round(self.price / 12, 2)
        return self.price

    @property
    def savings_vs_monthly(self):
        """Percentage saved vs monthly plan (for yearly)."""
        try:
            monthly = SubscriptionPlan.objects.get(slug='premium-monthly', is_active=True)
            yearly_monthly_equiv = self.price / 12
            return max(0, round((1 - yearly_monthly_equiv / monthly.price) * 100))
        except SubscriptionPlan.DoesNotExist:
            return 0


class UserSubscription(models.Model):
    """Tracks a user's active or expired subscription."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending Payment'),
        ('trial', 'Trial'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan        = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at  = models.DateTimeField(null=True, blank=True)
    expires_at  = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    auto_renew  = models.BooleanField(default=False)

    # Payment reference
    payment_gateway = models.CharField(max_length=50, blank=True, default='manual')
    gateway_sub_id  = models.CharField(max_length=200, blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        """True if the subscription is active and not expired."""
        if self.status != 'active':
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    @property
    def days_remaining(self):
        if not self.expires_at:
            return None
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)

    def activate(self):
        """Mark subscription active and set expiry from plan duration."""
        self.status     = 'active'
        self.started_at = timezone.now()
        self.expires_at = timezone.now() + timezone.timedelta(days=self.plan.duration_days)
        self.save(update_fields=['status', 'started_at', 'expires_at', 'updated_at'])

    def cancel(self):
        self.status       = 'cancelled'
        self.cancelled_at = timezone.now()
        self.auto_renew   = False
        self.save(update_fields=['status', 'cancelled_at', 'auto_renew', 'updated_at'])


class PaymentRecord(models.Model):
    """Immutable log of every payment attempt."""
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
        ('refunded', 'Refunded'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payment_records')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    plan         = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    currency     = models.CharField(max_length=3, default='INR')
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway      = models.CharField(max_length=50, default='manual')  # razorpay | stripe | upi
    gateway_order_id   = models.CharField(max_length=200, blank=True)
    gateway_payment_id = models.CharField(max_length=200, blank=True)
    gateway_signature  = models.CharField(max_length=500, blank=True)
    failure_reason     = models.TextField(blank=True)
    metadata           = models.JSONField(default=dict, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — ₹{self.amount} ({self.status})"


class AddressAccessRequest(models.Model):
    """
    Tracks when a premium renter requests to see a listing owner's exact address.
    Owner must approve before address is revealed.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='address_requests_made')
    owner     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='address_requests_received')
    listing   = models.ForeignKey('listings.Product', on_delete=models.CASCADE, related_name='address_requests')
    status    = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    owner_note   = models.CharField(max_length=300, blank=True)

    class Meta:
        unique_together = ('requester', 'listing')
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.requester.username} → {self.listing.title} ({self.status})"

    def approve(self, note=''):
        self.status       = 'approved'
        self.responded_at = timezone.now()
        self.owner_note   = note
        self.save(update_fields=['status', 'responded_at', 'owner_note'])

    def deny(self, note=''):
        self.status       = 'denied'
        self.responded_at = timezone.now()
        self.owner_note   = note
        self.save(update_fields=['status', 'responded_at', 'owner_note'])


class DailyMessageCount(models.Model):
    """Rolling daily counter for free-user message limit."""
    user  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_msg_counts')
    date  = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} — {self.date} — {self.count} messages"
