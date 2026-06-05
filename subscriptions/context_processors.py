"""
subscriptions/context_processors.py
------------------------------------
Injects premium status into every template context.
Fully guarded — never raises even if tables don't exist yet.
"""
from .utils import premium_context

_SAFE_DEFAULT = {
    'user_is_premium': False,
    'active_subscription': None,
    'premium_days_remaining': None,
    'daily_messages_used': 0,
    'daily_message_limit': 10,
}


def premium_processor(request):
    """Inject premium status into every template."""
    try:
        if not request.user.is_authenticated:
            return dict(_SAFE_DEFAULT)
        return premium_context(request.user)
    except Exception:
        # Absolute fallback — never break a page over subscription status
        return dict(_SAFE_DEFAULT)
