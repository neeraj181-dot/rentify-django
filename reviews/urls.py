from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:booking_pk>/', views.create_review_view, name='create_review'),
    path('my/', views.my_reviews_view, name='my_reviews'),
]
