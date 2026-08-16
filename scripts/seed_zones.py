import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from barber.models import Zone

def seed_zones():
    # 1. Eski zonalarni tozalash
    Zone.objects.all().delete()
    print("Eski zonalar tozalandi.")

    # 2. Yangi zonalarni yaratish
    zones = [
        {
            'name': 'Oddiy zona',
            'description': '3-4 kishilik umumiy navbat',
            'price': 0,
            'icon': '🆓',
            'type': 'ordinary',
            'capacity': 4,
            'is_active': True
        },
        {
            'name': 'VIP zona',
            'description': 'Alohida qulay zona',
            'price': 150000,
            'icon': '👑',
            'type': 'vip',
            'capacity': 1,
            'is_active': True
        }
    ]

    for z_data in zones:
        Zone.objects.create(**z_data)
        print(f"Zona yaratildi: {z_data['name']}")

    print("Barcha zonalar muvaffaqiyatli saqlandi!")

if __name__ == '__main__':
    seed_zones()
