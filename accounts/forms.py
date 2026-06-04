from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    UserCreationForm, AuthenticationForm, PasswordChangeForm,
    PasswordResetForm, SetPasswordForm
)
from .models import UserProfile


# ── shared widget helper ──────────────────────────────────────────────────────
def _inp(placeholder='', extra_class='', input_type='text', **attrs):
    base = 'auth-input'
    if extra_class:
        base += f' {extra_class}'
    return forms.TextInput(attrs={'placeholder': placeholder, 'class': base, **attrs})


def _email(placeholder=''):
    return forms.EmailInput(attrs={'placeholder': placeholder, 'class': 'auth-input'})


def _pwd(placeholder=''):
    return forms.PasswordInput(attrs={
        'placeholder': placeholder,
        'class': 'auth-input',
        'autocomplete': 'new-password',
    })


# ── Register ──────────────────────────────────────────────────────────────────
class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=_inp('First name'),
    )
    last_name = forms.CharField(
        max_length=30, required=True,
        widget=_inp('Last name'),
    )
    email = forms.EmailField(
        required=True,
        widget=_email('Email address'),
    )
    phone = forms.CharField(
        max_length=20, required=False,
        widget=_inp('+91 98765 43210'),
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'phone',
                  'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = _inp('Choose a username')
        self.fields['password1'].widget = _pwd('Create a strong password')
        self.fields['password2'].widget = _pwd('Confirm your password')
        # Remove Django's verbose help texts
        for f in ('username', 'password1', 'password2'):
            self.fields[f].help_text = ''

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Save phone to profile
            phone = self.cleaned_data.get('phone', '')
            if phone and hasattr(user, 'profile'):
                user.profile.phone = phone
                user.profile.save(update_fields=['phone'])
        return user


# ── Login ─────────────────────────────────────────────────────────────────────
class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = _inp('Email or username')
        self.fields['username'].label = 'Email or Username'
        self.fields['password'].widget = forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'auth-input',
        })

    def clean_username(self):
        raw = self.cleaned_data.get('username', '').strip()
        # Allow login with email
        if '@' in raw:
            try:
                user = User.objects.get(email__iexact=raw)
                return user.username
            except User.DoesNotExist:
                pass
        return raw


# ── Profile Update ────────────────────────────────────────────────────────────
class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
    )

    class Meta:
        model = UserProfile
        fields = ('phone', 'address', 'bio', 'profile_photo')
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 98765 43210',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, State',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell others about yourself — what you rent, your interests...',
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name
        self.fields['email'].initial = user.email

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        return email


# ── Password Change ───────────────────────────────────────────────────────────
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'old_password': 'Current password',
            'new_password1': 'New password',
            'new_password2': 'Confirm new password',
        }
        for name, ph in placeholders.items():
            self.fields[name].widget = forms.PasswordInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': ph,
            })
            self.fields[name].help_text = ''


# ── Password Reset ────────────────────────────────────────────────────────────
class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget = forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your email address',
        })


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('new_password1', 'new_password2'):
            self.fields[name].widget = forms.PasswordInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'New password' if '1' in name else 'Confirm new password',
            })
            self.fields[name].help_text = ''
