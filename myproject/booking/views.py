from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from .models import Service, Booking, Review, PaymentProof
from .forms import BookingForm, ReviewForm, RegisterForm, LoginForm, PaymentProofForm, ServiceForm

def index(request):
    top_services = Service.objects.all()
    return render(request, 'index.html', {'top_services': top_services})

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def services(request):
    if request.user.is_authenticated and request.user.role == 'provider':
        services = Service.objects.filter(manager=request.user)
    else:
        services = Service.objects.all()
    return render(request, 'services.html', {'services': services})

def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    bookings = Booking.objects.filter(service=service)
    reviews = Review.objects.filter(booking__in=bookings)
    context = {
        'service': service,
        'reviews': reviews
    }
    return render(request, 'services_detail.html', context)

@login_required
def booking(request, booking_id):
    service = get_object_or_404(Service, id=booking_id)
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.service = service
            booking.customer = request.user
            booking.save()
            return redirect('thank_you', booking_id=booking.id)
    else:
        form = BookingForm()
    return render(request, 'booking.html', {'form': form, 'service': service})

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
        messages.error(request, 'You are not authorized to access the provider dashboard.')
        return redirect('index')
    services = Service.objects.filter(manager=request.user)
    bookings = Booking.objects.filter(service__manager=request.user).order_by('-date')
    reviews = Review.objects.filter(booking__service__manager=request.user).order_by('-created_at')
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.manager = request.user
            service.save()
            messages.success(request, 'Service added successfully!')
            return redirect('provider_dashboard')
    else:
        form = ServiceForm()
    return render(request, 'provider_dashboard.html', {
        'services': services,
        'bookings': bookings,
        'form': form,
        'reviews': reviews
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
    if request.user.role != 'provider':
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('index')
    booking = get_object_or_404(Booking, id=booking_id, service__manager=request.user)
    if request.method == 'POST' and booking.status == 'pending':
        booking.status = 'confirmed'
        booking.save()
        messages.success(request, f'Booking {booking.id} confirmed successfully.')
    else:
        messages.error(request, 'This booking cannot be confirmed.')
    return redirect('provider_dashboard')

@login_required
def deny_booking(request, booking_id):
    if request.user.role != 'provider':
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('index')
    booking = get_object_or_404(Booking, id=booking_id, service__manager=request.user)
    if request.method == 'POST' and booking.status == 'pending':
        booking.status = 'cancelled'
        booking.save()
        messages.error(request, f'Booking {booking.id} cancelled successfully.')
    else:
        messages.error(request, 'This booking cannot be cancelled.')
    return redirect('provider_dashboard')

@login_required
@transaction.atomic
def approve_payment_proof(request, proof_id):
    if request.user.role != 'provider':
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('index')
    payment_proof = get_object_or_404(PaymentProof, id=proof_id, booking__service__manager=request.user)
    if request.method == 'POST' and payment_proof.status == 'pending' and payment_proof.booking.status == 'confirmed':
        payment_proof.status = 'approved'
        payment_proof.save()
        provider = request.user
        service_price = payment_proof.booking.service.price
        provider.wallet_balance += service_price
        provider.save()
        messages.success(request, f'Payment proof for booking {payment_proof.booking.id} approved. Rs. {service_price} added to your wallet.')
    else:
        messages.error(request, 'This payment proof cannot be approved.')
    return redirect('upload_payment_proof')

@login_required
def reject_payment_proof(request, proof_id):
    if request.user.role != 'provider':
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('index')
    payment_proof = get_object_or_404(PaymentProof, id=proof_id, booking__service__manager=request.user)
    if request.method == 'POST' and payment_proof.status == 'pending' and payment_proof.booking.status == 'confirmed':
        payment_proof.status = 'rejected'
        payment_proof.save()
        messages.error(request, f'Payment proof for booking {payment_proof.booking.id} rejected.')
    else:
        messages.error(request, 'This payment proof cannot be rejected.')
    return redirect('upload_payment_proof')