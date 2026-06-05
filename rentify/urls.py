from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import health_check, premium_view, premium_dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/health', health_check, name='health_check'),
    path('api/health/', health_check, name='health_check_slash'),
    path('premium/', premium_view, name='premium'),
    path('premium/dashboard/', premium_dashboard_view, name='premium_dashboard'),

    path('', include('listings.urls')),

    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),

    path('bookings/', include('bookings.urls')),
    path('messaging/', include('messaging.urls')),
    path('reviews/', include('reviews.urls')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
