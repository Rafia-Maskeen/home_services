from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Booking, Review, PaymentProof, CustomUser, Service,ProviderService, City


# -------------------- Register Form --------------------
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control w-full p-3 rounded-xl border border-gray-300',
        }),
        required=True,
        initial='customer',
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password1', 'password2', 'role']

# -------------------- Login Form --------------------
class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

# -------------------- Booking Form --------------------
class BookingForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full p-3 rounded-xl border border-gray-300',
        })
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full p-3 rounded-xl border border-gray-300',
        })
    )

    class Meta:
        model = Booking
        fields = ['date', 'time']

# -------------------- Review Form --------------------
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control w-full p-3 rounded-xl border border-gray-300',
                'rows': 4,
                'placeholder': 'Write your review here...'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control w-full p-3 rounded-xl border border-gray-300',
                'min': 1,
                'max': 5,
                'placeholder': 'Rate from 1 to 5'
            }),
        }

# -------------------- Payment Proof Form --------------------
class PaymentProofForm(forms.ModelForm):
    booking = forms.ModelChoiceField(
        queryset=Booking.objects.none(),
        empty_label="Select a booking",
        widget=forms.Select(attrs={
            'class': 'w-full p-3 rounded-xl border border-gray-300',
        })
    )

    class Meta:
        model = PaymentProof
        fields = ['booking', 'file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'w-full p-3 rounded-xl border border-gray-300',
                'accept': 'image/*,application/pdf'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['booking'].queryset = (
                Booking.objects
                .filter(customer=user, status='awaiting_payment')
                .select_related(
                    'provider_service',
                    'provider_service__provider',
                    'provider_service__service'
                )
            )
# -------------------- Service Form --------------------
class ProviderServiceForm(forms.ModelForm):
    class Meta:
        model = ProviderService
        fields = ['service', 'city']
        widgets = {
            'service': forms.Select(attrs={'class': 'w-full p-3 rounded-xl border'}),
            'city': forms.Select(attrs={'class': 'w-full p-3 rounded-xl border'}),
           
        }


# -------------------- Complete Service Form --------------------
# forms.py
class CompleteServiceForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['final_price']

    final_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        label="Final Service Price (Rs.)"
    )


