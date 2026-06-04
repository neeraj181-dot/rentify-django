from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Booking
from .forms import BookingForm
from listings.models import Product
from notifications.utils import create_notification
from decimal import Decimal


@login_required
def create_booking_view(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk, is_available=True, is_flagged=False)

    if product.owner == request.user:
        messages.error(request, "You cannot rent your own product.")
        return redirect('product_detail', pk=product_pk)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.renter = request.user
            booking.product = product
            booking.calculate_total()
            booking.save()

            # Notify owner
            create_notification(
                recipient=product.owner,
                sender=request.user,
                notification_type='booking_request',
                message=f"{request.user.get_full_name() or request.user.username} wants to rent your '{product.title}'",
                link=f'/bookings/owner/'
            )
            messages.success(request, 'Booking request sent! The owner will review it shortly.')
            return redirect('booking_detail', pk=booking.pk)
    else:
        form = BookingForm()

    context = {'form': form, 'product': product}
    return render(request, 'bookings/create_booking.html', context)


@login_required
def booking_detail_view(request, pk):
    booking = Booking.objects.select_related('product', 'renter', 'product__owner').get(pk=pk)
    # Only renter or owner can view
    if request.user != booking.renter and request.user != booking.product.owner:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    return render(request, 'bookings/booking_detail.html', {'booking': booking})


@login_required
def my_bookings_view(request):
    bookings = Booking.objects.filter(renter=request.user).select_related('product').order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def owner_bookings_view(request):
    bookings = Booking.objects.filter(
        product__owner=request.user
    ).select_related('product', 'renter').order_by('-created_at')
    pending = bookings.filter(status='pending')
    active = bookings.filter(status__in=['approved', 'active'])
    history = bookings.filter(status__in=['completed', 'rejected', 'cancelled'])
    context = {
        'pending': pending,
        'active': active,
        'history': history,
        'all_bookings': bookings,
    }
    return render(request, 'bookings/owner_bookings.html', context)


@login_required
def approve_booking_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk, product__owner=request.user, status='pending')
    booking.status = 'approved'
    booking.owner_note = request.POST.get('owner_note', '')
    booking.save()
    create_notification(
        recipient=booking.renter,
        sender=request.user,
        notification_type='booking_approved',
        message=f"Your booking for '{booking.product.title}' has been approved!",
        link=f'/bookings/{booking.pk}/'
    )
    messages.success(request, f'Booking approved for {booking.renter.username}.')
    return redirect('owner_bookings')


@login_required
def reject_booking_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk, product__owner=request.user, status='pending')
    booking.status = 'rejected'
    booking.owner_note = request.POST.get('owner_note', '')
    booking.save()
    create_notification(
        recipient=booking.renter,
        sender=request.user,
        notification_type='booking_rejected',
        message=f"Your booking for '{booking.product.title}' was not approved.",
        link=f'/bookings/{booking.pk}/'
    )
    messages.info(request, 'Booking rejected.')
    return redirect('owner_bookings')


@login_required
def mark_returned_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk, product__owner=request.user, status='approved')
    booking.status = 'completed'
    booking.save()
    # Update owner earnings
    profile = request.user.profile
    profile.total_earnings += booking.rental_cost
    profile.save()
    create_notification(
        recipient=booking.renter,
        sender=request.user,
        notification_type='product_returned',
        message=f"'{booking.product.title}' has been marked as returned. Please leave a review!",
        link=f'/reviews/create/{booking.pk}/'
    )
    messages.success(request, 'Product marked as returned. Rental completed!')
    return redirect('owner_bookings')


@login_required
def cancel_booking_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk, renter=request.user, status__in=['pending', 'approved'])
    booking.status = 'cancelled'
    booking.save()
    messages.info(request, 'Booking cancelled.')
    return redirect('my_bookings')


def calculate_price_ajax(request):
    """AJAX endpoint to calculate booking cost dynamically."""
    try:
        product_id = request.GET.get('product_id')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        from datetime import date
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        product = Product.objects.get(pk=product_id)
        total_days = (end - start).days + 1
        if total_days <= 0:
            return JsonResponse({'error': 'Invalid dates'}, status=400)

        if total_days >= 30 and product.price_per_month:
            months = total_days / 30
            rental_cost = float(Decimal(str(months)) * product.price_per_month)
        elif total_days >= 7 and product.price_per_week:
            weeks = total_days / 7
            rental_cost = float(Decimal(str(weeks)) * product.price_per_week)
        else:
            rental_cost = float(total_days * product.price_per_day)

        deposit = float(product.security_deposit)
        return JsonResponse({
            'total_days': total_days,
            'rental_cost': rental_cost,
            'deposit': deposit,
            'total': rental_cost + deposit,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
