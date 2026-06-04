from django.db import models
from django.contrib.auth.models import User
from listings.models import Product
from bookings.models import Booking
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    reviewee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review', null=True, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('reviewer', 'booking')

    def __str__(self):
        return f"{self.reviewer.username} → {self.reviewee.username}: {self.rating}★"

    def get_stars(self):
        return range(self.rating)

    def get_empty_stars(self):
        return range(5 - self.rating)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_product_rating()
        self._update_user_rating()

    def _update_product_rating(self):
        if self.product:
            from django.db.models import Avg
            result = Review.objects.filter(product=self.product).aggregate(avg=Avg('rating'))
            self.product.rating = result['avg'] or 0
            self.product.total_reviews = Review.objects.filter(product=self.product).count()
            self.product.save(update_fields=['rating', 'total_reviews'])

    def _update_user_rating(self):
        from django.db.models import Avg
        result = Review.objects.filter(reviewee=self.reviewee).aggregate(avg=Avg('rating'))
        profile = self.reviewee.profile
        profile.rating = result['avg'] or 0
        profile.total_reviews = Review.objects.filter(reviewee=self.reviewee).count()
        profile.save(update_fields=['rating', 'total_reviews'])
