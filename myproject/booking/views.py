from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.db.models import Avg
from django.http import JsonResponse
from .models import (
    Service,
    ProviderService,
    Booking,
    Review,
    PaymentProof,
    City,
    CustomUser
)
from .forms import (
    BookingForm,
    ReviewForm,
    RegisterForm,
    LoginForm,
    PaymentProofForm,
    ProviderServiceForm,
    CompleteServiceForm,
)

def index(request):
    top_services = Service.objects.all()[:8]  # or any number you want
    return render(request, 'index.html', {
        'top_services': top_services
    })




def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def services(request):
    services = Service.objects.all()
    return render(request, 'services.html', {
        'services': services
    })


def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    city_id = request.GET.get('city')
    providers = ProviderService.objects.filter(
        service=service,
        is_active=True
    )

    if city_id:
        providers = providers.filter(city_id=city_id)

    cities = City.objects.all()

    return render(request, 'services_detail.html', {
        'service': service,
        'providers': providers,
        'cities': cities,
    })

@login_required
def create_booking(request, provider_service_id):
    provider_service = get_object_or_404(
        ProviderService,
        id=provider_service_id,
        is_active=True
    )

    if request.user.role != 'customer':
        messages.error(request, 'Only customers can book services.')
        return redirect('index')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.provider_service = provider_service
            booking.status = 'pending'
            booking.save()

            return redirect('thank_you', booking_id=booking.id)
    else:
        form = BookingForm()

    return render(request, 'booking.html', {
        'form': form,
        'provider_service': provider_service
    })


@login_required
def thank_you(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'thank_you.html', {'booking': booking})

@login_required
def submit_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if hasattr(booking, 'review'):
        messages.error(request, "You have already submitted a review for this booking.")
        return redirect('thank_you', booking_id=booking_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.save()
            messages.success(request, "Thank you for your review!")
            return redirect('thank_you', booking_id=booking_id)
    else:
        form = ReviewForm()
    return render(request, 'submit_review.html', {'form': form, 'booking': booking})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.role == 'provider':
                return redirect('provider_dashboard')
            return redirect('customer_dashboard')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.role == 'provider':
                    return redirect('provider_dashboard')
                return redirect('customer_dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def custom_logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect('login')
    return render(request, 'logout.html')

@login_required
def provider_dashboard(request):
    if request.user.role != 'provider':
        return redirect('index')

    offerings = ProviderService.objects.filter(provider=request.user)

    bookings = (
        Booking.objects
        .filter(provider_service__provider=request.user)
        .select_related(
            'customer',
            'provider_service__service',
            'provider_service__city',
        )
        .order_by('-date')
    )

    # ✅ FETCH REVIEWS CORRECTLY
    reviews = (
        Review.objects
        .filter(booking__provider_service__provider=request.user)
        .select_related(
            'booking__customer',
            'booking__provider_service__service'
        )
        .order_by('-created_at')
    )

    if request.method == 'POST':
        form = ProviderServiceForm(request.POST)
        if form.is_valid():
            ps = form.save(commit=False)
            ps.provider = request.user
            ps.save()
            messages.success(request, 'Service added successfully.')
            return redirect('provider_dashboard')
    else:
        form = ProviderServiceForm()

    return render(request, 'provider_dashboard.html', {
        'offerings': offerings,
        'bookings': bookings,
        'reviews': reviews,   # ✅ THIS WAS MISSING
        'form': form,
    })


@login_required
def customer_dashboard(request):
    if request.user.role != 'customer':
        messages.error(request, 'You are not authorized to access the customer dashboard.')
        return redirect('index')
    bookings = Booking.objects.filter(customer=request.user).order_by('-date')
    reviews = Review.objects.filter(booking__customer=request.user).order_by('-created_at')
    return render(request, 'customer_dashboard.html', {
        'bookings': bookings,
        'reviews': reviews
    })

@login_required
def upload_payment_proof(request, booking_id=None):
    if request.user.role == 'customer':
        if request.method == 'POST':
            form = PaymentProofForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                payment_proof = form.save(commit=False)
                payment_proof.customer = request.user
                if booking_id:
                    payment_proof.booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
                payment_proof.save()
                messages.success(request, 'Payment proof uploaded successfully!')
                return redirect('customer_dashboard')
        else:
            form = PaymentProofForm(user=request.user)
        payment_proofs = PaymentProof.objects.filter(customer=request.user).order_by('-upload_date')
        context = {
            'form': form,
            'payment_proofs': payment_proofs,
        }
        if booking_id:
            context['booking'] = get_object_or_404(Booking, id=booking_id, customer=request.user)
    else:
        payment_proofs = PaymentProof.objects.filter(booking__service__manager=request.user).order_by('-upload_date')
        total_earnings = request.user.wallet_balance
        context = {
            'payment_proofs': payment_proofs,
            'total_earnings': total_earnings,
        }
    return render(request, 'upload_payment_proof.html', context)

@login_required
def accept_booking(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        provider_service__provider=request.user,
        status='pending'
    )

    if request.method == 'POST':
        booking.status = 'confirmed'
        booking.save()
        messages.success(request, "Booking confirmed.")

    return redirect('provider_dashboard')


@login_required
def deny_booking(request, booking_id):
    if request.user.role != 'provider':
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('index')
    booking = get_object_or_404(
    Booking,
    id=booking_id,
    provider_service__provider=request.user
)

    if request.method == 'POST' and booking.status == 'pending':
        booking.status = 'cancelled'
        booking.save()
        messages.error(request, f'Booking {booking.id} cancelled successfully.')
    else:
        messages.error(request, 'This booking cannot be cancelled.')
    return redirect('provider_dashboard')
@login_required
@transaction.atomic
def complete_booking(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        provider_service__provider=request.user,
        status='confirmed'
    )

    if request.method == 'POST':
        form = CompleteServiceForm(request.POST, instance=booking)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.status = 'awaiting_payment'
            booking.save()

            messages.success(request, "Service completed. Awaiting payment.")
            return redirect('provider_dashboard')
    else:
        form = CompleteServiceForm(instance=booking)

    return render(request, 'complete_booking.html', {
        'form': form,
        'booking': booking
    })



@login_required
@transaction.atomic
def approve_payment_proof(request, proof_id):
    proof = get_object_or_404(
        PaymentProof,
        id=proof_id,
        booking__provider_service__provider=request.user,
        status='pending'
    )

    booking = proof.booking
    provider = booking.provider_service.provider

    proof.status = 'approved'
    booking.status = 'completed'
    provider.wallet_balance += booking.final_price

    proof.save()
    booking.save()
    provider.save()

    messages.success(request, "Payment approved successfully.")
    return redirect('provider_payments')


@login_required
def reject_payment_proof(request, proof_id):
    if request.user.role != 'provider':
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('index')
    payment_proof = get_object_or_404(
    PaymentProof,
    id=proof_id,
    booking__provider_service__provider=request.user
)

    if request.method == 'POST' and payment_proof.status == 'pending' and payment_proof.booking.status == 'awaiting_payment':
        payment_proof.status = 'rejected'
        payment_proof.save()
        messages.error(request, f'Payment proof for booking {payment_proof.booking.id} rejected.')
    else:
        messages.error(request, 'This payment proof cannot be rejected.')
    return redirect('upload_payment_proof')

@login_required
def customer_polling(request):
    if request.user.role != 'customer':
        return JsonResponse({"error": "Unauthorized"}, status=403)

    bookings = (
        Booking.objects
        .filter(customer=request.user)
        .select_related(
            'provider_service__service',
            'provider_service__provider',
            'provider_service__city',
        )
        .order_by('-date')
    )

    data = []

    for booking in bookings:
        proof = PaymentProof.objects.filter(booking=booking).first()

        data.append({
            "booking_id": booking.id,
            "service": booking.provider_service.service.title,
            "provider": booking.provider_service.provider.username,
            "city": booking.provider_service.city.name,
            "booking_status": booking.status,
            "payment_status": proof.status if proof else None,
            "price": str(booking.final_price),
            "date": booking.date.strftime("%Y-%m-%d"),
            "time": booking.time.strftime("%H:%M"),
        })

    return JsonResponse({"bookings": data})


@login_required
def provider_polling(request):
    if request.user.role != 'provider':
        return JsonResponse({"error": "Unauthorized"}, status=403)

    bookings = (
        Booking.objects
        .filter(provider_service__provider=request.user)
        .select_related(
            'customer',
            'provider_service__service',
            'provider_service__city',
        )
        .order_by('-date')
    )

    data = []

    for booking in bookings:
        proof = PaymentProof.objects.filter(booking=booking).first()

        data.append({
            "booking_id": booking.id,
            "customer": booking.customer.username,
            "service": booking.provider_service.service.title,
            "city": booking.provider_service.city.name,
            "booking_status": booking.status,
            "payment_status": proof.status if proof else None,
            "price": str(booking.final_price),
            "date": booking.date.strftime("%Y-%m-%d"),
            "time": booking.time.strftime("%H:%M"),
        })

    return JsonResponse({"bookings": data})

@login_required
def provider_services(request):
    if request.user.role != 'provider':
        messages.error(request, "Unauthorized access")
        return redirect('index')

    provider_services = (
        ProviderService.objects
        .filter(provider=request.user)
        .select_related('service', 'city')
    )

    return render(request, 'provider_services.html', {
        'provider_services': provider_services
    })


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related(
            'provider_service__service',
            'provider_service__provider',
            'provider_service__city',
            'customer',
        ),
        id=booking_id
    )

    # 🔐 Security check
    if (
        request.user != booking.customer and
        request.user != booking.provider_service.provider
    ):
        messages.error(request, "You are not allowed to view this booking.")
        return redirect('index')

    return render(request, 'booking_detail.html', {
        'booking': booking
    })




def provider_profile(request, provider_id):
    provider = get_object_or_404(
        CustomUser,
        id=provider_id,
        role='provider'
    )

    services = Service.objects.filter(manager=provider)

    average_rating = Review.objects.filter(
        booking__service__manager=provider
    ).aggregate(avg=Avg('rating'))['avg']

    return render(request, 'booking/provider_profile.html', {
        'provider': provider,
        'services': services,
        'average_rating': round(average_rating, 1) if average_rating else None
    })

@login_required
def provider_payments(request):
    if request.user.role != 'provider':
        return redirect('index')

    proofs = (
        PaymentProof.objects
        .filter(
            booking__provider_service__provider=request.user,
            status='pending'
        )
        .select_related('booking__customer', 'booking__provider_service__service')
    )

    return render(request, 'provider_payments.html', {
        'proofs': proofs
    })
