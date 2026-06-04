from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('how-it-works/', views.how_it_works_view, name='how_it_works'),
    path('categories/', views.categories_page_view, name='categories_page'),
    path('earn/', views.earn_view, name='earn'),
    path('browse/', views.search_view, name='browse'),
    path('search/', views.search_view, name='search'),
    path('category/<str:category_slug>/', views.category_view, name='category_detail'),
    path('listings/new/', views.create_listing_view, name='create_listing'),
    path('listings/my/', views.my_listings_view, name='my_listings'),
    path('listings/<int:pk>/', views.product_detail_view, name='product_detail'),
    path('listings/<int:pk>/edit/', views.edit_listing_view, name='edit_listing'),
    path('listings/<int:pk>/delete/', views.delete_listing_view, name='delete_listing'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:pk>/', views.toggle_wishlist_view, name='toggle_wishlist'),
    path('images/<int:image_id>/delete/', views.delete_product_image, name='delete_product_image'),
    path('images/<int:image_id>/set-cover/', views.set_primary_image, name='set_primary_image'),
    path('api/listing-form-meta/', views.listing_form_meta, name='listing_form_meta'),
    path('api/locations/', views.location_counts_api, name='location_counts_api'),
    path('api/set-location/', views.set_browse_location_view, name='set_browse_location'),
    path('api/reverse-geocode/', views.reverse_geocode_view, name='reverse_geocode'),
    path('api/ai/price-suggestion/', views.ai_price_suggestion, name='ai_price_suggestion'),
    path('api/ai/description/', views.ai_description_generator, name='ai_description'),
]
