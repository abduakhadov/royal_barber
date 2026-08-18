from django.urls import path
from . import views

app_name = 'barber'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/zones/', views.get_zones, name='zones'),
    path('api/services/', views.get_services, name='services'),
    path('api/barbers/', views.get_barbers, name='barbers'),
    path('api/available-slots/', views.get_available_slots, name='slots'),
    path('api/book/', views.book_appointment, name='book'),
    path('api/my-bookings/', views.get_my_bookings, name='my_bookings'),
    path('api/cancel-booking/', views.cancel_booking_api, name='cancel_booking'),
    path('api/send-otp/', views.send_otp_api, name='send_otp'),
    path('api/verify-otp/', views.verify_otp_api, name='verify_otp'),
]


