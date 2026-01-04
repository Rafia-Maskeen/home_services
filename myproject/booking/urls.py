# booking/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # -------- Public pages --------
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # -------- Services & Providers --------
    path('services/', views.services, name='services'),  # list all services
    path('services/<int:service_id>/', views.service_detail, name='service_detail'),

    # -------- Booking flow (Customer) --------
    path(
        'book/<int:provider_service_id>/',
        views.create_booking,
        name='create_booking'
    ),
    path('thank-you/<int:booking_id>/', views.thank_you, name='thank_you'),
    path('submit-review/<int:booking_id>/', views.submit_review, name='submit_review'),
# booking/urls.py
path(
    'provider/services/',
    views.provider_services,
    name='provider_services'
),
path(
    'booking/detail/<int:booking_id>/',
    views.booking_detail,
    name='booking_detail'
),

    # -------- Auth --------
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.custom_logout_view, name='logout'),

    # -------- Dashboards --------
    path('provider/dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),

    # -------- Payment Proofs --------
    path('payments/upload/', views.upload_payment_proof, name='upload_payment_proof'),
    path(
        'payments/upload/<int:booking_id>/',
        views.upload_payment_proof,
        name='upload_payment_proof'
    ),
    path('provider/payments/', views.provider_payments, name='provider_payments'),
    path('provider/payment/approve/<int:proof_id>/', views.approve_payment_proof, name='approve_payment'),
    path('provider/payment/approve/<int:proof_id>/', views.approve_payment_proof, name='approve_payment_proof'),
    path('provider/payment/reject/<int:proof_id>/', views.reject_payment_proof, name='reject_payment_proof'),


    # -------- Provider Actions --------
    path(
        'provider/booking/confirm/<int:booking_id>/',
        views.accept_booking,
        name='accept_booking'
    ),
    path(
        'provider/booking/cancel/<int:booking_id>/',
        views.deny_booking,
        name='deny_booking'
    ),
    path(
        'provider/booking/complete/<int:booking_id>/',
        views.complete_booking,
        name='complete_booking'
    ),

    # -------- Payment Moderation --------
    path(
        'provider/payment/approve/<int:proof_id>/',
        views.approve_payment_proof,
        name='approve_payment_proof'
    ),
    path(
        'provider/payment/reject/<int:proof_id>/',
        views.reject_payment_proof,
        name='reject_payment_proof'
    ),

    # -------- Polling APIs --------
    path(
        'api/customer/polling/',
        views.customer_polling,
        name='customer_polling'
    ),
    path(
        'api/provider/polling/',
        views.provider_polling,
        name='provider_polling'
    ),
    path(
    'provider/<int:provider_id>/',
    views.provider_profile,
    name='provider_profile'
),

]
