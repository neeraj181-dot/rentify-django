from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('booking_request', 'Booking Request'),
        ('booking_approved', 'Booking Approved'),
        ('booking_rejected', 'Booking Rejected'),
        ('new_message', 'New Message'),
        ('product_returned', 'Product Returned'),
        ('new_review', 'New Review'),
        ('general', 'General'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='general')
    message = models.TextField()
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"→ {self.recipient.username}: {self.message[:60]}"

    def get_icon(self):
        icons = {
            'booking_request': 'bi-calendar-plus',
            'booking_approved': 'bi-check-circle-fill',
            'booking_rejected': 'bi-x-circle-fill',
            'new_message': 'bi-chat-dots-fill',
            'product_returned': 'bi-box-arrow-in-down',
            'new_review': 'bi-star-fill',
            'general': 'bi-bell-fill',
        }
        return icons.get(self.notification_type, 'bi-bell')

    def get_color(self):
        colors = {
            'booking_request': 'primary',
            'booking_approved': 'success',
            'booking_rejected': 'danger',
            'new_message': 'info',
            'product_returned': 'secondary',
            'new_review': 'warning',
            'general': 'secondary',
        }
        return colors.get(self.notification_type, 'secondary')
