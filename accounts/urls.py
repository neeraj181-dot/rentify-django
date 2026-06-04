from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomPasswordResetForm, CustomSetPasswordForm

urlpatterns = [
    # Core auth
    path('register/',         views.register_view,      name='register'),
    path('login/',            views.login_view,          name='login'),
    path('logout/',           views.logout_view,         name='logout'),
    path('api/session/',      views.session_status_view, name='session_status'),
    path('api/logout/',       views.api_logout_view,     name='api_logout'),

    # Dashboard & profile
    path('dashboard/',        views.dashboard_view,      name='dashboard'),
    path('profile/edit/',     views.edit_profile_view,   name='edit_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('profile/<str:username>/',  views.public_profile_view,  name='public_profile'),

    # Dark mode
    path('toggle-dark-mode/', views.toggle_dark_mode,    name='toggle_dark_mode'),

    # AJAX
    path('check/',            views.check_availability,  name='check_availability'),

    # ── Password Reset (Django built-in views + custom templates) ──
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             form_class=CustomPasswordResetForm,
             email_template_name='accounts/email/password_reset_email.html',
             subject_template_name='accounts/email/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/',
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('password-reset/confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             form_class=CustomSetPasswordForm,
             success_url='/accounts/password-reset/complete/',
         ),
         name='password_reset_confirm'),

    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),
]
