from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.templatetags.static import static


CATEGORY_CHOICES = [
    ('laptops', 'Laptops'),
    ('cameras', 'Cameras'),
    ('gaming', 'Gaming'),
    ('drones', 'Drones'),
    ('bikes', 'Bikes'),
    ('cars', 'Cars'),
    ('furniture', 'Furniture'),
    ('tools', 'Tools'),
    ('books', 'Books'),
    ('musical_instruments', 'Music'),
    ('projectors', 'Projectors'),
    ('other', 'Other'),
]

CATEGORY_ICONS = {
    'laptops': 'bi-laptop',
    'cameras': 'bi-camera',
    'drones': 'bi-controller',
    'gaming': 'bi-joystick',
    'bikes': 'bi-bicycle',
    'cars': 'bi-car-front',
    'furniture': 'bi-house',
    'books': 'bi-book',
    'tools': 'bi-tools',
    'projectors': 'bi-projector',
    'musical_instruments': 'bi-music-note-beamed',
    'other': 'bi-grid',
}


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='bi-grid')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField()
    location = models.CharField(max_length=200, help_text='Public display: city/area only')
    state = models.CharField(max_length=100, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    area_locality = models.CharField(max_length=120, blank=True, default='')
    address_private = models.CharField(max_length=300, blank=True, default='')
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_week = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_available = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'pk': self.pk})

    def get_category_display_name(self):
        return dict(CATEGORY_CHOICES).get(self.category, 'Other')

    def get_category_icon(self):
        return CATEGORY_ICONS.get(self.category, 'bi-grid')

    def get_primary_image(self):
        img = self.images.filter(is_primary=True).first() or self.images.first()
        return img.image.url if img else static('images/no-image.svg')

    def auto_calculate_prices(self):
        if not self.price_per_week:
            self.price_per_week = self.price_per_day * 6
        if not self.price_per_month:
            self.price_per_month = self.price_per_day * 25

    def build_public_location(self):
        """City/area shown on listings — never includes private address."""
        parts = []
        if self.area_locality and self.area_locality.strip():
            parts.append(self.area_locality.strip())
        if self.city and self.city.strip():
            if not parts or self.city.strip().lower() != parts[0].lower():
                parts.append(self.city.strip())
        if parts:
            return ', '.join(parts)
        return (self.location or '').strip()

    def sync_public_location(self):
        built = self.build_public_location()
        if built:
            self.location = built

    def get_public_location(self):
        return self.build_public_location() or self.location or ''


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f"Image for {self.product.title}"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"
