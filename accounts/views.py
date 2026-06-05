from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Avg
from django.conf import settings
import json
import logging
import jwt
import datetime

from .forms import (
    RegisterForm, LoginForm, ProfileUpdateForm,
    CustomPasswordChangeForm, CustomPasswordResetForm, CustomSetPasswordForm,
)
from .models import UserProfile
from .auth_utils import user_session_payload
from listings.models import Product
from bookings.models import Booking
from reviews.models import Review
from messaging.models import Message

logger = logging.getLogger(__name__)


# ── AJAX helpers ──────────────────────────────────────────────────────────────
def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _auth_redirect_url(request):
    """Return a safe post-login redirect — stay on marketplace pages when possible."""
    for key in ('next',):
        candidate = request.POST.get(key) or request.GET.get(key, '')
        if candidate.startswith('/') and 'login' not in candidate and 'register' not in candidate:
            return candidate
    referer = request.META.get('HTTP_REFERER', '')
    if referer:
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        path = parsed.path
        if path.startswith('/') and 'login' not in path and 'register' not in path:
            return path + (f'?{parsed.query}' if parsed.query else '')
    return '/accounts/dashboard/'


# ── Health Check ──────────────────────────────────────────────────────────────
def health_check(request):
    return JsonResponse({'status': 'ok'})


# ── Register ──────────────────────────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated and not _is_ajax(request):
        return redirect('dashboard')

    if request.method == 'POST':
        # Log incoming registration request
        ip_address = request.META.get('REMOTE_ADDR')
        logger.info("Incoming registration request from IP: %s", ip_address)
        
        # Log payload (scrubbed of passwords)
        log_payload = request.POST.copy()
        log_payload.pop('password1', None)
        log_payload.pop('password2', None)
        log_payload.pop('csrfmiddlewaretoken', None)
        logger.info("Registration request payload: %s", dict(log_payload))

        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            name = user.first_name or user.username
            messages.success(request, f'Welcome to Rentify, {name}! Your account is ready.')
            
            # Generate JWT token
            token_payload = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }
            jwt_token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm='HS256')
            logger.info("Successful registration: User %s (ID: %s). JWT Token generated: %s", user.username, user.id, jwt_token)

            redirect_to = _auth_redirect_url(request)
            if _is_ajax(request):
                return JsonResponse({
                    'ok': True,
                    'redirect': redirect_to,
                })
            return redirect(redirect_to)
        else:
            # Log validation errors
            logger.warning("Registration validation errors: %s", form.errors.as_json())
            if _is_ajax(request):
                errors = {f: e.get_json_data() for f, e in form.errors.items()}
                return JsonResponse({'ok': False, 'errors': errors}, status=400)
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})



# ── Login ─────────────────────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated and not _is_ajax(request):
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            remember = request.POST.get('remember_me')
            if not remember:
                request.session.set_expiry(0)
            login(request, user)
            name = user.first_name or user.username
            messages.success(request, f'Welcome back, {name}!')
            redirect_to = _auth_redirect_url(request)
            if _is_ajax(request):
                return JsonResponse({'ok': True, 'redirect': redirect_to})
            return redirect(redirect_to)
        else:
            if _is_ajax(request):
                return JsonResponse({'ok': False, 'error': 'Invalid username/email or password.'}, status=400)
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


# ── Logout ────────────────────────────────────────────────────────────────────
def _clear_session(request, response=None):
    """Fully destroy Django session and session cookie."""
    logout(request)
    request.session.flush()
    if response is None:
        response = redirect('home')
    response.delete_cookie(
        settings.SESSION_COOKIE_NAME,
        path=settings.SESSION_COOKIE_PATH or '/',
        domain=settings.SESSION_COOKIE_DOMAIN,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )
    return response


def logout_view(request):
    """Sign out — works even when session is partially invalid."""
    response = _clear_session(request)
    messages.info(request, 'You have been signed out.')
    return response


@require_GET
@ensure_csrf_cookie
def session_status_view(request):
    """Validate auth on startup — Django session only (no localStorage JWT)."""
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': user_session_payload(request.user),
        })
    return JsonResponse({'authenticated': False})


@require_POST
def api_logout_view(request):
    """AJAX logout — clear session without requiring an active login."""
    response = JsonResponse({'ok': True})
    return _clear_session(request, response)


# ── Dashboard ─────────────────────────────────────────────────────────────────
@login_required
def dashboard_view(request):
    user = request.user
    my_listings       = Product.objects.filter(owner=user)
    pending_requests  = Booking.objects.filter(product__owner=user, status='pending')
    active_rentals    = Booking.objects.filter(product__owner=user, status='approved')
    my_bookings       = Booking.objects.filter(renter=user).select_related('product').order_by('-created_at')[:5]
    total_earnings    = user.profile.total_earnings
    recent_bookings   = Booking.objects.filter(product__owner=user).order_by('-created_at')[:5]
    my_rentals_active = Booking.objects.filter(
        renter=user, status__in=['pending', 'approved', 'active']
    ).count()
    messages_unread = Message.objects.filter(
        conversation__participants=user,
        is_read=False,
    ).exclude(sender=user).count()

    context = {
        'my_listings':        my_listings,
        'my_listings_count':  my_listings.count(),
        'pending_requests':   pending_requests,
        'pending_count':      pending_requests.count(),
        'active_rentals_count': active_rentals.count(),
        'my_rentals_active':  my_rentals_active,
        'my_bookings':        my_bookings,
        'total_earnings':     total_earnings,
        'recent_bookings':    recent_bookings,
        'messages_unread':    messages_unread,
    }
    return render(request, 'accounts/dashboard.html', context)


# ── Public Profile ────────────────────────────────────────────────────────────
def public_profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    listings     = Product.objects.filter(owner=profile_user, is_available=True)
    reviews      = Review.objects.filter(reviewee=profile_user).select_related('reviewer').order_by('-created_at')
    avg_rating   = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    can_view_contact = False
    if request.user.is_authenticated:
        can_view_contact = request.user == profile_user or request.user.profile.is_premium

    return render(request, 'accounts/public_profile.html', {
        'profile_user': profile_user,
        'listings':     listings,
        'reviews':      reviews,
        'avg_rating':   avg_rating,
        'review_count': reviews.count(),
        'can_view_contact': can_view_contact,
    })


# ── Edit Profile ──────────────────────────────────────────────────────────────
@login_required
def edit_profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.user, request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name  = form.cleaned_data['last_name']
            request.user.email      = form.cleaned_data['email']
            request.user.save()
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('dashboard')
    else:
        form = ProfileUpdateForm(request.user, instance=profile)
    return render(request, 'accounts/edit_profile.html', {'form': form})


# ── Change Password ───────────────────────────────────────────────────────────
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated successfully.')
            return redirect('dashboard')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


# ── Dark Mode Toggle ──────────────────────────────────────────────────────────
@login_required
def toggle_dark_mode(request):
    profile = request.user.profile
    profile.dark_mode = not profile.dark_mode
    profile.save(update_fields=['dark_mode'])
    return redirect(request.META.get('HTTP_REFERER', '/'))


def premium_view(request):
    is_premium = False
    if request.user.is_authenticated:
        is_premium = getattr(request.user, 'profile', None) and request.user.profile.is_premium

    return render(request, 'accounts/premium.html', {
        'is_premium': is_premium,
    })


def premium_dashboard_view(request):
    profile = None
    is_premium = False
    messages_used = 0
    messages_limit = 0
    messages_remaining = 0
    
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        is_premium = bool(profile and profile.is_premium)
        messages_used = profile.messages_sent_count if profile else 0
        messages_limit = float('inf') if is_premium else 5
        messages_remaining = max(0, int(messages_limit) - messages_used) if not is_premium else float('inf')

    return render(request, 'accounts/premium_dashboard.html', {
        'is_premium': is_premium,
        'premium_status_label': 'Premium Active' if is_premium else 'Premium Not Active',
        'messages_used': messages_used,
        'messages_limit': messages_limit if messages_limit != float('inf') else 'Unlimited',
        'messages_remaining': messages_remaining if messages_remaining != float('inf') else 'Unlimited',
        'current_plan': 'Premium' if is_premium else 'Free',
    })


# ── AJAX: check username / email availability ─────────────────────────────────
def check_availability(request):
    field = request.GET.get('field')
    value = request.GET.get('value', '').strip()
    if field == 'username':
        taken = User.objects.filter(username__iexact=value).exists()
    elif field == 'email':
        taken = User.objects.filter(email__iexact=value).exists()
    else:
        return JsonResponse({'error': 'invalid field'}, status=400)
    return JsonResponse({'available': not taken})
