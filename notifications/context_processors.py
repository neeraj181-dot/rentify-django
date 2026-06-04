from .models import Notification


def notifications_processor(request):
    """Inject notifications + footer data into every template context."""
    ctx = {
        'unread_notifications': [],
        'unread_count': 0,
        'user_listings_count': 0,
        'user_wishlist_count': 0,
        'user_messages_unread': 0,
        'footer_sections': _footer_sections(request),
    }
    if request.user.is_authenticated:
        user = request.user
        ctx['unread_notifications'] = Notification.objects.filter(
            recipient=user, is_read=False
        ).order_by('-created_at')[:8]
        ctx['unread_count'] = Notification.objects.filter(
            recipient=user, is_read=False
        ).count()
        ctx.update(_user_menu_stats(user))
    return ctx


def _user_menu_stats(user):
    """Counts for profile dropdown quick stats (read-only queries)."""
    from listings.models import Product, Wishlist
    from messaging.models import Message

    listings_count = Product.objects.filter(owner=user).count()
    wishlist_count = Wishlist.objects.filter(user=user).count()
    messages_unread = Message.objects.filter(
        conversation__participants=user,
        is_read=False,
    ).exclude(sender=user).count()

    return {
        'user_listings_count': listings_count,
        'user_wishlist_count': wishlist_count,
        'user_messages_unread': messages_unread,
    }


def _footer_sections(request):
    user = getattr(request, 'user', None)
    authed = user and user.is_authenticated
    explore = [
        ('Browse All', '/browse/'),
        ('Laptops', '/category/laptops/'),
        ('Cameras', '/category/cameras/'),
        ('Bikes',   '/category/bikes/'),
        ('Gaming',  '/category/gaming/'),
    ]
    account = [
        ('Dashboard',   '/accounts/dashboard/')  if authed else ('Sign Up', '/accounts/register/'),
        ('My Listings', '/listings/my/')          if authed else ('Sign In', '/accounts/login/'),
        ('My Rentals',  '/bookings/my/')          if authed else None,
        ('Wishlist',    '/wishlist/')              if authed else None,
    ]
    account = [a for a in account if a]
    company = [
        ('About Us',    '#'),
        ('How It Works', '/how-it-works/'),
        ('Safety',      '#'),
        ('Contact',     '#'),
    ]
    legal = [
        ('Privacy Policy',  '#'),
        ('Terms of Service','#'),
        ('Cookie Policy',   '#'),
    ]
    return [
        ('Explore',  explore),
        ('Account',  account),
        ('Company',  company),
        ('Legal',    legal),
    ]
