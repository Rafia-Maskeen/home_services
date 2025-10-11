from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('provider', 'Service Provider'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.username

class ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='services')
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    manager = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='services')

    def __str__(self):
        return self.title


class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.service.title} - {self.customer.username}"

class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.booking}"

class PaymentProof(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payment_proofs')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payment_proofs')
    file = models.FileField(upload_to='payment_proofs/')
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Payment proof for {self.booking} by {self.customer.username}"