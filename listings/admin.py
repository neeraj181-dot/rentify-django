from django.contrib import admin
from .models import Product, ProductImage, Wishlist, Category


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('uploaded_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'price_per_day', 'is_available', 'is_flagged', 'rating', 'created_at')
    list_filter = ('category', 'is_available', 'is_flagged')
    search_fields = ('title', 'owner__username', 'location')
    list_editable = ('is_available', 'is_flagged')
    inlines = [ProductImageInline]
    readonly_fields = ('views_count', 'rating', 'total_reviews', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {'fields': ('owner', 'title', 'category', 'description', 'location')}),
        ('Pricing', {'fields': ('price_per_day', 'price_per_week', 'price_per_month', 'security_deposit')}),
        ('Status', {'fields': ('is_available', 'is_flagged', 'flag_reason')}),
        ('Stats', {'fields': ('rating', 'total_reviews', 'views_count', 'created_at', 'updated_at')}),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'order', 'uploaded_at')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
