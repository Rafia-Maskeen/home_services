from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import CustomUser, Service, Booking, Review, PaymentProof, ServiceType, City, ProviderService
from django.db import transaction

User = get_user_model()

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


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
    list_display = ('id', 'title', 'service_type')
    search_fields = ('title', 'description')
    list_filter = ('service_type',)

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'provider_service',
        'date',
        'time',
        'status',
        'final_price'
    )
    list_filter = ('status', 'date')
    search_fields = (
        'customer__username',
        'provider_service__service__title',
        'provider_service__provider__username'
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(provider_service__provider=request.user)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return obj and obj.provider_service.provider == request.user

    def has_delete_permission(self, request, obj=None):
        return False

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
    list_filter = ('status',)

    actions = ['approve_payment']

    @admin.action(description="Approve payment")
    def approve_payment(self, request, queryset):
        with transaction.atomic():
            for proof in queryset.select_related(
                'booking__provider_service__provider'
            ):
                if proof.status != 'approved':
                    booking = proof.booking
                    provider = booking.provider_service.provider
                    amount = booking.final_price

                    proof.status = 'approved'
                    booking.status = 'completed'
                    provider.wallet_balance += amount

                    proof.save()
                    booking.save()
                    provider.save()

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(ProviderService)
class ProviderServiceAdmin(admin.ModelAdmin):
    list_display = ('provider', 'service', 'city', 'price', 'is_active')
    list_filter = ('city', 'service', 'is_active')
    search_fields = ('provider__username', 'service__title')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(provider=request.user)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.provider = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields['provider'].disabled = True
            form.base_fields['provider'].initial = request.user
        return form
