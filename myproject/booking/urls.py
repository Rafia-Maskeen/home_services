# booking/urls.py

from django.urls import path
from . import views
from .views import custom_logout_view


urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
     path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    path('booking/<int:booking_id>/', views.booking, name='booking'),
    path('submit-review/<int:booking_id>/', views.submit_review, name='submit_review'),
    path('thank-you/<int:booking_id>/', views.thank_you, name='thank_you'),
    path('login/', views.user_login, name='login'),
    
    path('register/', views.register, name='register'),
    path('logout/', custom_logout_view, name='logout'),
    path('provider/dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('booking/<int:booking_id>/upload-payment/', views.upload_payment_proof, name='upload_payment_proof_specific'),
    path('upload-payment/', views.upload_payment_proof, name='upload_payment_proof'),
    path('accept-booking/<int:booking_id>/', views.accept_booking, name='accept_booking'),
    path('deny-booking/<int:booking_id>/', views.deny_booking, name='deny_booking'),
    path('approve-payment-proof/<int:proof_id>/', views.approve_payment_proof, name='approve_payment_proof'),
    path('reject-payment-proof/<int:proof_id>/', views.reject_payment_proof, name='reject_payment_proof'),
    
]
    

    



