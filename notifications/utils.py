from .models import Notification


def create_notification(recipient, sender, notification_type, message, link=''):
    """Helper to create a notification safely."""
    if recipient == sender:
        return None
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        message=message,
        link=link,
    )
