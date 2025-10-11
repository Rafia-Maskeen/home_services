from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import CustomUser, Service, Booking, Review, PaymentProof, ServiceType
from django.db import transaction

User = get_user_model()

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role', 'wallet_balance', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'email']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'wallet_balance')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'wallet_balance')}),
    )

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'manager', 'service_type', 'price')
    search_fields = ('title', 'description', 'manager__username')
    list_filter = ('service_type',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(manager=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'manager' in form.base_fields:
                form.base_fields['manager'].initial = request.user
                form.base_fields['manager'].disabled = True
        return form

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.manager = request.user
        obj.save()

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'service', 'date', 'time', 'status', 'completion_price')
    list_filter = ('status', 'date', 'service')
    search_fields = ('customer__username', 'service__title')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(service__manager=request.user)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return obj is not None and obj.service.manager == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return obj is not None and obj.service.manager == request.user

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'created_at')
    search_fields = ('booking__id', 'comment')
    list_filter = ('rating', 'created_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(booking__service__manager=request.user)

@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ('booking', 'customer', 'status', 'upload_date')
    list_filter = ('status', 'upload_date')
    search_fields = ('booking__service__title', 'customer__username')
    actions = ['approve_payment_proofs']

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == 'approved':
            return [f.name for f in self.model._meta.fields if f.name != 'status']
        return []

    @admin.action(description='Approve selected payment proofs')
    def approve_payment_proofs(self, request, queryset):
        with transaction.atomic():
            for payment_proof in queryset:
                if payment_proof.status != 'approved' and payment_proof.booking.status == 'awaiting_payment':
                    payment_proof.status = 'approved'
                    payment_proof.booking.status = 'completed'
                    payment_proof.save()
                    payment_proof.booking.save()
                    provider = payment_proof.booking.service.manager
                    service_price = payment_proof.booking.completion_price or payment_proof.booking.service.price
                    provider.wallet_balance += service_price
                    provider.save()
                    self.message_user(
                        request,
                        f'The payment proof for booking {payment_proof.booking.id} was approved successfully and Rs. {service_price} added to {provider.username}\'s wallet.'
                    )

    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data and obj.status == 'approved' and obj.booking.status == 'awaiting_payment':
            obj.booking.status = 'completed'
            obj.booking.save()
            provider = obj.booking.service.manager
            service_price = obj.booking.completion_price or obj.booking.service.price
            provider.wallet_balance += service_price
            provider.save()
            self.message_user(
                request,
                f'The payment proof for booking {obj.booking.id} was approved successfully and Rs. {service_price} added to {provider.username}\'s wallet.'
            )
        super().save_model(request, obj, form, change)

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)