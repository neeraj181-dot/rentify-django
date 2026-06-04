from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache
from .models import Booking
from .forms import BookingForm
from listings.models import Product
from notifications.utils import create_notification
from decimal import Decimal


def _no_cache(response):
    """Add headers that stop the browser caching a page so Back never shows a stale form."""
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma']  = 'no-cache'
    response['Expires'] = '0'
    return response


@never_cache
@login_required
def create_booking_view(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk, is_available=True, is_flagged=False)

    # Cannot book own listing
    if product.owner == request.user:
        messages.error(request, "You cannot rent your own listing.")
        return redirect('product_detail', pk=product_pk)

    # ── Duplicate-booking guard ──────────────────────────────────────────────
    # Block if any non-terminal booking exists for this product+renter combo.
    # Forward-compatible: also blocks future payment-flow statuses.
    BLOCK_STATUSES = ('pending', 'approved', 'active', 'awaiting_payment', 'paid')
    existing = Booking.objects.filter(
        renter=request.user,
        product=product,
        status__in=BLOCK_STATUSES,
    ).first()
    if existing:
        messages.warning(
            request,
            f"You already have an active booking request for '{product.title}' "
            f"(status: {existing.get_status_display()}). "
            f"Cancel it first if you want to make a new request."
        )
        return redirect('booking_detail', pk=existing.pk)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            # Race-condition double-submit guard (e.g. double-click the button)
            if Booking.objects.filter(
                renter=request.user, product=product, status__in=BLOCK_STATUSES
            ).exists():
                messages.warning(request, "A booking for this item already exists.")
                return redirect('my_bookings')

            booking = form.save(commit=False)
            booking.renter  = request.user
            booking.product = product
            booking.calculate_total()
            booking.save()

            create_notification(
                recipient=product.owner,
                sender=request.user,
                notification_type='booking_request',
                message=(
                    f"{request.user.get_full_name() or request.user.username} "
                    f"wants to rent your '{product.title}'"
                ),
                link='/bookings/owner/',
            )
            messages.success(request, '✓ Booking request sent! The owner will review it shortly.')
            # PRG — 303 redirect so Back button never re-submits the form
            return HttpResponseRedirect(
                reverse('my_bookings') if hasattr(request, '_use_reverse') else '/bookings/my/',
                status=303,
            )
    else:
        form = BookingForm()

    response = render(request, 'bookings/create_booking.html', {'form': form, 'product': product})
    return _no_cache(response)


@login_required
def booking_detail_view(request, pk):
    booking = Booking.objects.select_related(
        'product', 'renter', 'product__owner'
    ).get(pk=pk)
    if request.user != booking.renter and request.user != booking.product.owner:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    return render(request, 'bookings/booking_detail.html', {'booking': booking})


@login_required
def my_bookings_view(request):
    bookings = Booking.objects.filter(
        renter=request.user
    ).select_related('product').order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def owner_bookings_view(request):
    bookings = Booking.objects.filter(
        product__owner=request.user
    ).select_related('product', 'renter').order_by('-created_at')
    pending = bookings.filter(status='pending')
    active  = bookings.filter(status__in=['approved', 'active'])
    history = bookings.filter(status__in=['completed', 'rejected', 'cancelled'])
    context = {
        'pending':      pending,
        'active':       active,
        'history':      history,
        'all_bookings': bookings,
    }
    return render(request, 'bookings/owner_bookings.html', context)


@login_required
def approve_booking_view(request, pk):
    booking = get_object_or_404(
        Booking, pk=pk, product__owner=request.user, status='pending'
    )
    booking.status     = 'approved'
    booking.owner_note = request.POST.get('owner_note', '')
    booking.save()
    create_notification(
        recipient=booking.renter,
        sender=request.user,
        notification_type='booking_approved',
        message=f"Your booking for '{booking.product.title}' has been approved!",
        link=f'/bookings/{booking.pk}/',
    )
    messages.success(request, f'Booking approved for {booking.renter.username}.')
    return redirect('owner_bookings')


@login_required
def reject_booking_view(request, pk):
    booking = get_object_or_404(
        Booking, pk=pk, product__owner=request.user, status='pending'
    )
    booking.status     = 'rejected'
    booking.owner_note = request.POST.get('owner_note', '')
    booking.save()
    create_notification(
        recipient=booking.renter,
        sender=request.user,
        notification_type='booking_rejected',
        message=f"Your booking for '{booking.product.title}' was not approved.",
        link=f'/bookings/{booking.pk}/',
    )
    messages.info(request, 'Booking declined.')
    return redirect('owner_bookings')


@login_required
def mark_returned_view(request, pk):
    booking = get_object_or_404(
        Booking, pk=pk, product__owner=request.user, status='approved'
    )
    booking.status = 'completed'
    booking.save()
    profile = request.user.profile
    profile.total_earnings += booking.rental_cost
    profile.save()
    create_notification(
        recipient=booking.renter,
        sender=request.user,
        notification_type='product_returned',
        message=f"'{booking.product.title}' marked as returned. Please leave a review!",
        link=f'/reviews/create/{booking.pk}/',
    )
    messages.success(request, 'Product marked as returned. Rental completed!')
    return redirect('owner_bookings')


@login_required
def cancel_booking_view(request, pk):
    booking = get_object_or_404(
        Booking, pk=pk, renter=request.user, status__in=['pending', 'approved']
    )
    booking.status = 'cancelled'
    booking.save()
    messages.info(request, 'Booking cancelled.')
    return redirect('my_bookings')


def calculate_price_ajax(request):
    """AJAX endpoint for live price calculation on booking form."""
    try:
        product_id = request.GET.get('product_id')
        start_date = request.GET.get('start_date')
        end_date   = request.GET.get('end_date')
        from datetime import date
        start   = date.fromisoformat(start_date)
        end     = date.fromisoformat(end_date)
        product = Product.objects.get(pk=product_id)
        total_days = (end - start).days + 1
        if total_days <= 0:
            return JsonResponse({'error': 'Invalid dates'}, status=400)

        if total_days >= 30 and product.price_per_month:
            rental_cost = float(Decimal(str(total_days / 30)) * product.price_per_month)
        elif total_days >= 7 and product.price_per_week:
            rental_cost = float(Decimal(str(total_days / 7)) * product.price_per_week)
        else:
            rental_cost = float(total_days * product.price_per_day)

        return JsonResponse({
            'total_days':  total_days,
            'rental_cost': rental_cost,
            'deposit':     float(product.security_deposit),
            'total':       rental_cost + float(product.security_deposit),
        })
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=400)
