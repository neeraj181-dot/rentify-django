"""
subscriptions/utils.py
----------------------
Single source of truth for all premium permission checks.
All DB calls are guarded against OperationalError so the app
degrades gracefully if migrations haven't run yet.
"""
from django.utils import timezone
from django.db import transaction, OperationalError, ProgrammingError

FREE_MESSAGE_DAILY_LIMIT = 10
FREE_WISHLIST_LIMIT = 20

# ── DB-safe wrapper ───────────────────────────────────────────────────────────

def _db_safe(fn, default=None):
    """Call fn(); return default on any DB / table-missing error."""
    try:
        return fn()
    except (OperationalError, ProgrammingError):
        return default
    except Exception:
        return default


# ── Core helpers ──────────────────────────────────────────────────────────────

def get_active_subscription(user):
    """Return the user's current active UserSubscription or None."""
    if not user or not user.is_authenticated:
        return None

    def _query():
        from .models import UserSubscription
        now = timezone.now()
        return (
            UserSubscription.objects
            .filter(user=user, status='active', expires_at__gt=now)
            .select_related('plan')
            .order_by('-expires_at')
            .first()
        )

    return _db_safe(_query)


def is_premium(user):
    """Boolean — does this user have a live premium subscription?"""
    return get_active_subscription(user) is not None


# ── Feature-level gates ───────────────────────────────────────────────────────

def can_send_message(user):
    """
    Returns (allowed: bool, remaining: int|None).
    Premium → always (True, None).
    Free → (True if under daily limit, remaining count).
    """
    if is_premium(user):
        return True, None

    def _query():
        from .models import DailyMessageCount
        today = timezone.localdate()
        obj, _ = DailyMessageCount.objects.get_or_create(user=user, date=today)
        remaining = max(0, FREE_MESSAGE_DAILY_LIMIT - obj.count)
        return remaining > 0, remaining

    result = _db_safe(_query, default=(True, FREE_MESSAGE_DAILY_LIMIT))
    return result


def record_message_sent(user):
    """Increment daily message counter for free users. No-op for premium."""
    if is_premium(user):
        return

    def _query():
        from .models import DailyMessageCount
        today = timezone.localdate()
        with transaction.atomic():
            obj, _ = DailyMessageCount.objects.select_for_update().get_or_create(
                user=user, date=today
            )
            obj.count += 1
            obj.save(update_fields=['count'])

    _db_safe(_query)


def can_add_to_wishlist(user, current_count):
    """Free users limited to FREE_WISHLIST_LIMIT items."""
    if is_premium(user):
        return True
    return current_count < FREE_WISHLIST_LIMIT


def can_view_contact_number(user):
    return is_premium(user)


def can_view_exact_address(user, listing):
    """
    True if:
      - user is the owner, or
      - user has a confirmed booking, or
      - user is premium AND has an approved AddressAccessRequest.
    """
    if not user or not user.is_authenticated:
        return False

    if listing.owner_id == user.id:
        return True

    def _booking_check():
        from bookings.models import Booking
        return Booking.objects.filter(
            renter=user, product=listing,
            status__in=['approved', 'active', 'completed'],
        ).exists()

    if _db_safe(_booking_check, default=False):
        return True

    if not is_premium(user):
        return False

    def _access_check():
        from .models import AddressAccessRequest
        return AddressAccessRequest.objects.filter(
            requester=user, listing=listing, status='approved'
        ).exists()

    return _db_safe(_access_check, default=False)


def can_use_advanced_filters(user):
    return is_premium(user)


def daily_messages_used_today(user):
    def _query():
        from .models import DailyMessageCount
        today = timezone.localdate()
        obj = DailyMessageCount.objects.filter(user=user, date=today).first()
        return obj.count if obj else 0

    return _db_safe(_query, default=0)


# ── Context dict for templates ────────────────────────────────────────────────

def premium_context(user):
    """
    Returns a dict to merge into template context.
    Used by the context processor and any view that needs premium info.
    """
    sub = get_active_subscription(user)
    return {
        'user_is_premium': sub is not None,
        'active_subscription': sub,
        'premium_days_remaining': sub.days_remaining if sub else None,
        'daily_messages_used': (
            daily_messages_used_today(user) if (user and user.is_authenticated) else 0
        ),
        'daily_message_limit': FREE_MESSAGE_DAILY_LIMIT,
    }
