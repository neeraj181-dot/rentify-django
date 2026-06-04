from django.urls import path
from . import views

urlpatterns = [
    path('book/<int:product_pk>/', views.create_booking_view, name='create_booking'),
    path('<int:pk>/', views.booking_detail_view, name='booking_detail'),
    path('my/', views.my_bookings_view, name='my_bookings'),
    path('owner/', views.owner_bookings_view, name='owner_bookings'),
    path('<int:pk>/approve/', views.approve_booking_view, name='approve_booking'),
    path('<int:pk>/reject/', views.reject_booking_view, name='reject_booking'),
    path('<int:pk>/returned/', views.mark_returned_view, name='mark_returned'),
    path('<int:pk>/cancel/', views.cancel_booking_view, name='cancel_booking'),
    path('api/calculate/', views.calculate_price_ajax, name='calculate_price'),
]
