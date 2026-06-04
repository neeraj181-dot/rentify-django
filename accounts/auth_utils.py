"""Auth helpers — session validation; no client-side trust without server check."""

AUTH_STORAGE_KEYS = (
    'rentify_token',
    'rfy-access-token',
    'rfy-refresh-token',
    'rfy-user',
    'rfy_user',
    'access_token',
    'refresh_token',
    'authToken',
    'user',
    'rentify_user',
    'rentify_auth',
)


def user_session_payload(user):
    profile = getattr(user, 'profile', None)
    return {
        'id': user.id,
        'username': user.username,
        'display_name': user.get_full_name() or user.username,
        'avatar': profile.get_photo_url() if profile else '',
        'email': user.email,
    }
