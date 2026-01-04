from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
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
    class Meta:
        model = Booking
        fields = ['date', 'time', 'address']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-3 rounded-xl border'
            }),
            'time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full p-3 rounded-xl border'
            }),
            'address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full p-3 rounded-xl border',
                'placeholder': 'Enter service address'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')

        if not date or not time:
            return cleaned_data

        now = timezone.now()

        # ❌ Past date
        if date < now.date():
            raise forms.ValidationError("You cannot select a past date.")

        # ❌ Past time if booking today
        if date == now.date() and time <= now.time():
            raise forms.ValidationError("You cannot select a past time.")

        return cleaned_data


# -------------------- Review Form --------------------
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'class': 'w-full p-3 rounded-xl border'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full p-3 rounded-xl border',
                'placeholder': 'Write your review here...'
            }),
        }


# -------------------- Payment Proof Form --------------------
class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = PaymentProof
        fields = ['booking', 'file']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            qs = Booking.objects.filter(
                customer=user,
                status='awaiting_payment'
            ).select_related('provider_service__service')

            self.fields['booking'].queryset = qs
            self.fields['booking'].label_from_instance = (
                lambda b: f"{b.provider_service.service.title} – {b.date} {b.time.strftime('%I:%M %p')}"
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
    final_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        label="Final Service Price (Rs.)",
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 rounded-xl border',
            'placeholder': 'Enter final service price'
        })
    )

    class Meta:
        model = Booking
        fields = ['final_price']



