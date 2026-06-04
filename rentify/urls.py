from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health', health_check, name='health_check'),
    path('api/health/', health_check, name='health_check_slash'),
    path('', include('listings.urls')),
    path('accounts/', include('accounts.urls')),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('bookings/', include('bookings.urls')),
    path('messaging/', include('messaging.urls')),
    path('reviews/', include('reviews.urls')),
    path('notifications/', include('notifications.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

