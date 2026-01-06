from django.core.mail import send_mail
from django.conf import settings


def send_booking_status_email(booking, status):
    subject = f"Booking {status.capitalize()} – {booking.provider_service.service.title}"

    message = f"""
Hello {booking.customer.username},

Your booking for "{booking.provider_service.service.title}" has been {status}.

Provider: {booking.provider_service.provider.username}
Date: {booking.date}
Time: {booking.time}

Thank you for using HomeService.
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.customer.email],
        fail_silently=False,
    )


def send_payment_status_email(proof, status):
    subject = f"Payment {status.capitalize()} – {proof.booking.provider_service.service.title}"

    message = f"""
Hello {proof.booking.customer.username},

Your payment for "{proof.booking.provider_service.service.title}" has been {status}.

Amount: Rs. {proof.booking.final_price}

Thank you for using HomeService.
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [proof.booking.customer.email],
        fail_silently=False,
    )
