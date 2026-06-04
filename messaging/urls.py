from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('<int:conv_id>/', views.conversation_view, name='conversation'),
    path('start/<str:username>/', views.start_conversation_view, name='start_conversation'),
    path('<int:conv_id>/poll/', views.get_new_messages, name='poll_messages'),
]
