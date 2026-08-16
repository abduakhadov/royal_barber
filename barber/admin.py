from django.contrib import admin
from .models import Customer, Barber, Service, Booking, Zone

@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'icon')
    search_fields = ('name',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'first_name', 'username', 'phone', 'created_at')
    search_fields = ('telegram_id', 'first_name', 'username', 'phone')

@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'specialty')
    search_fields = ('name', 'specialty')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_minutes', 'icon')
    search_fields = ('name',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer', 'barber', 'service', 'zone', 'date', 'time_slot', 'status', 'is_paid')
    list_filter = ('status', 'date', 'is_paid', 'zone')
    search_fields = ('customer__first_name', 'barber__name', 'service__name')

