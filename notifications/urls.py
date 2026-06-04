from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list_view, name='notifications_list'),
    path('<int:pk>/read/', views.mark_read_view, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('api/unread-count/', views.unread_count_api, name='unread_count_api'),
]
