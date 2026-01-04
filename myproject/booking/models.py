from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('provider', 'Service Provider'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def is_provider(self):
        return self.role == 'provider'


class ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='services/', blank=True, null=True)

    def __str__(self):
        return self.title

class ProviderService(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    provider = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('awaiting_payment', 'Awaiting Payment'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
)

class Booking(models.Model):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    provider_service = models.ForeignKey(ProviderService, on_delete=models.CASCADE)

    date = models.DateField()
    time = models.TimeField()
    address = models.TextField(blank=True)  # 👈 allow blank

    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(
        default=timezone.now,   # ✅ IMPORTANT
        editable=False
    )






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

    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='payment_proofs'
    )

    file = models.FileField(
        upload_to='payment_proofs/',
        blank=True,
        null=True
    )

    upload_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    def approve(self):
        """Admin approval hook"""
        self.status = 'approved'
        self.save()

        # ✅ MARK BOOKING AS PAID
        self.booking.is_paid = True
        self.booking.status = 'confirmed'
        self.booking.save()

    def __str__(self):
        return f"Payment for {self.booking.provider_service.service.title}"

