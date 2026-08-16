from django.db import models

class Zone(models.Model):
    ZONE_TYPES = [
        ('ordinary', 'Oddiy'),
        ('vip', 'VIP'),
    ]
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    icon = models.CharField(max_length=10, default="🪑")
    type = models.CharField(max_length=20, choices=ZONE_TYPES, default='ordinary')
    capacity = models.IntegerField(default=4)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.icon} {self.name} - {int(self.price):,} UZS"

class Customer(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} ({self.telegram_id})"

class Barber(models.Model):
    name = models.CharField(max_length=100)
    photo_url = models.CharField(max_length=500, default="https://images.unsplash.com/photo-1517832606299-7ae9b720a186?q=80&w=120&auto=format&fit=crop")
    rating = models.FloatField(default=4.9)
    specialty = models.CharField(max_length=150, default="Erkaklar sartaroshi")

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField(default=30)
    icon = models.CharField(max_length=10, default="✂️")

    def __str__(self):
        return f"{self.icon} {self.name} - {int(self.price):,} UZS"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('confirmed', 'Tasdiqlandi'),
        ('cancelled', 'Bekor qilindi'),
        ('completed', 'Yakunlandi'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='bookings')
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    date = models.DateField()
    time_slot = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_paid = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.time_slot and hasattr(self, 'service') and self.service:
            import datetime
            dt = datetime.datetime.combine(datetime.date.today(), self.time_slot)
            dt += datetime.timedelta(minutes=self.service.duration_minutes)
            self.end_time = dt.time()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.first_name} - {self.barber.name} ({self.date} {self.time_slot})"
