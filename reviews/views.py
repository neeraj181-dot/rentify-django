from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review
from .forms import ReviewForm
from bookings.models import Booking
from notifications.utils import create_notification


@login_required
def create_review_view(request, booking_pk):
    booking = get_object_or_404(Booking, pk=booking_pk, renter=request.user, status='completed')

    if hasattr(booking, 'review'):
        messages.info(request, 'You have already reviewed this rental.')
        return redirect('booking_detail', pk=booking_pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.reviewee = booking.product.owner
            review.product = booking.product
            review.booking = booking
            review.save()
            create_notification(
                recipient=booking.product.owner,
                sender=request.user,
                notification_type='new_review',
                message=f"{request.user.username} left a {review.rating}★ review for '{booking.product.title}'",
                link=f'/listings/{booking.product.pk}/'
            )
            messages.success(request, 'Review submitted! Thank you.')
            return redirect('booking_detail', pk=booking_pk)
    else:
        form = ReviewForm()

    return render(request, 'reviews/create_review.html', {
        'form': form,
        'booking': booking,
        'product': booking.product,
    })


@login_required
def my_reviews_view(request):
    given = Review.objects.filter(reviewer=request.user).select_related('product', 'reviewee')
    received = Review.objects.filter(reviewee=request.user).select_related('product', 'reviewer')
    return render(request, 'reviews/my_reviews.html', {'given': given, 'received': received})
