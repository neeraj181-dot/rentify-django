from django.db import models
from django.contrib.auth.models import User
from listings.models import Product
from decimal import Decimal


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField(default=1)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    rental_cost = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    renter_note = models.TextField(blank=True)
    owner_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.renter.username} → {self.product.title} ({self.status})"

    def calculate_total(self):
        self.total_days = (self.end_date - self.start_date).days + 1
        if self.total_days <= 0:
            self.total_days = 1
        self.price_per_day = self.product.price_per_day
        self.security_deposit = self.product.security_deposit

        # Apply weekly/monthly discount
        if self.total_days >= 30 and self.product.price_per_month:
            months = self.total_days / 30
            self.rental_cost = Decimal(str(months)) * self.product.price_per_month
        elif self.total_days >= 7 and self.product.price_per_week:
            weeks = self.total_days / 7
            self.rental_cost = Decimal(str(weeks)) * self.product.price_per_week
        else:
            self.rental_cost = Decimal(str(self.total_days)) * self.price_per_day

        self.total_amount = self.rental_cost + self.security_deposit

    def get_status_badge(self):
        badges = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'active': 'primary',
            'completed': 'secondary',
            'cancelled': 'dark',
        }
        return badges.get(self.status, 'secondary')

    def get_status_icon(self):
        icons = {
            'pending': 'bi-clock',
            'approved': 'bi-check-circle',
            'rejected': 'bi-x-circle',
            'active': 'bi-play-circle',
            'completed': 'bi-check2-all',
            'cancelled': 'bi-dash-circle',
        }
        return icons.get(self.status, 'bi-circle')
