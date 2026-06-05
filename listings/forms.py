from django import forms
from .models import Product, ProductImage, CATEGORY_CHOICES
from .location_data import INDIAN_STATES

FIELD = 'rfy-field-input'
TEXTAREA = 'rfy-field-input rfy-field-textarea'


class ProductForm(forms.ModelForm):
    state = forms.ChoiceField(
        choices=(),
        widget=forms.Select(attrs={
            'class': f'{FIELD} rfy-field-select',
            'id': 'id_state',
        })
    )

    class Meta:
        model = Product
        fields = [
            'title', 'category', 'description',
            'state', 'city', 'area_locality', 'address_private',
            'price_per_day', 'price_per_week', 'price_per_month',
            'security_deposit', 'is_available',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': FIELD,
                'placeholder': 'e.g. MacBook Air M3, Canon EOS R5...',
            }),
            'category': forms.Select(attrs={'class': f'{FIELD} rfy-field-select'}),
            'description': forms.Textarea(attrs={
                'class': TEXTAREA,
                'rows': 5,
                'placeholder': "Describe your product — condition, features, what's included...",
            }),
            'city': forms.TextInput(attrs={
                'class': FIELD,
                'id': 'id_city',
                'placeholder': 'e.g. Kochi, Malappuram',
                'autocomplete': 'address-level2',
            }),
            'area_locality': forms.TextInput(attrs={
                'class': FIELD,
                'placeholder': 'e.g. Edappally, Downtown',
                'autocomplete': 'address-level3',
            }),
            'address_private': forms.Textarea(attrs={
                'class': TEXTAREA,
                'rows': 2,
                'placeholder': 'Full address — only visible to you & confirmed renters',
                'autocomplete': 'street-address',
            }),
            'price_per_day': forms.NumberInput(attrs={
                'class': FIELD, 'placeholder': '0.00', 'min': '0', 'step': '0.01',
            }),
            'price_per_week': forms.NumberInput(attrs={
                'class': FIELD, 'placeholder': 'Auto-calculated', 'min': '0', 'step': '0.01',
            }),
            'price_per_month': forms.NumberInput(attrs={
                'class': FIELD, 'placeholder': 'Auto-calculated', 'min': '0', 'step': '0.01',
            }),
            'security_deposit': forms.NumberInput(attrs={
                'class': FIELD, 'placeholder': '0.00', 'min': '0', 'step': '0.01',
            }),
            'is_available': forms.CheckboxInput(attrs={'class': 'rfy-toggle'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['state'].choices = INDIAN_STATES
        self.fields['state'].required = True
        self.fields['city'].required = True
        self.fields['area_locality'].required = True
        self.fields['address_private'].required = False
        self.fields['address_private'].label = 'Address (optional, private)'

        # Legacy listings: pre-fill city from old location string
        if self.instance and self.instance.pk and not self.instance.city and self.instance.location:
            self.initial.setdefault('city', self.instance.location)

    def clean(self):
        cleaned = super().clean()
        city = (cleaned.get('city') or '').strip()
        area = (cleaned.get('area_locality') or '').strip()
        state = (cleaned.get('state') or '').strip()
        if not state:
            self.add_error('state', 'Please select a state.')
        if not city:
            self.add_error('city', 'City or district is required.')
        if not area:
            self.add_error('area_locality', 'Area or locality is required.')
        return cleaned

    def clean_price_per_day(self):
        price = self.cleaned_data.get('price_per_day')
        if price and price <= 0:
            raise forms.ValidationError('Price must be greater than 0.')
        return price

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.sync_public_location()
        if commit:
            instance.save()
        return instance


class ProductImageForm(forms.ModelForm):
    """Single-image upload form — submit multiple times or use the inline formset."""
    class Meta:
        model = ProductImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            })
        }


class SearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Search for laptops, cameras, bikes...'
        })
    )
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'All Categories')] + list(CATEGORY_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'})
    )
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min ₹'})
    )
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max ₹'})
    )
    min_rating = forms.ChoiceField(
        required=False,
        choices=[('', 'Any Rating'), ('4', '4+ Stars'), ('3', '3+ Stars'), ('2', '2+ Stars')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    available_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
