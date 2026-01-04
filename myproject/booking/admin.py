from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
from .models import (
    CustomUser,
    Service,
    Booking,
    Review,
    PaymentProof,
    ServiceType,
    City,
    ProviderService,
)

User = get_user_model()


# -------------------- City --------------------
@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


# -------------------- Custom User --------------------
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        'username',
        'email',
        'role',
        'wallet_balance',
        'is_active',
        'date_joined',
    )
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'email')

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'wallet_balance')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'wallet_balance')}),
    )


# -------------------- Service --------------------
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'service_type')
    search_fields = ('title', 'description')
    list_filter = ('service_type',)

    # 🔒 Only superadmin manages services
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# -------------------- Booking --------------------
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'provider_service',
        'date',
        'time',
        'status',
        'final_price',
    )
    list_filter = ('status', 'date')
    search_fields = (
        'customer__username',
        'provider_service__service__title',
        'provider_service__provider__username',
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


# -------------------- Review --------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('booking__id', 'comment')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # ✅ FIXED RELATION
        return qs.filter(
            booking__provider_service__provider=request.user
        )


# -------------------- Payment Proof --------------------
@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ("booking", "customer", "status", "upload_date")
    list_filter = ("status",)
    actions = ["approve_payment"]

    @admin.action(description="Approve payment")
    def approve_payment(self, request, queryset):
        with transaction.atomic():
            for proof in queryset.select_related(
                "booking__provider_service__provider"
            ):
                # 🔒 prevent double approval
                if proof.status == "approved":
                    continue

                booking = proof.booking
                provider = booking.provider_service.provider

                # ❌ Do not allow approval without final price
                if booking.final_price is None:
                    continue

                # ✅ HARD SAFETY
                provider.wallet_balance = (
                    provider.wallet_balance or Decimal("0.00")
                )

                provider.wallet_balance += booking.final_price

                proof.status = "approved"
                booking.status = "completed"

                provider.save(update_fields=["wallet_balance"])
                booking.save(update_fields=["status"])
                proof.save(update_fields=["status"])



# -------------------- Service Type --------------------
@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


# -------------------- Provider Service --------------------
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
