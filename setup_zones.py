import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from barber.models import Zone

def setup_zones():
    Zone.objects.get_or_create(
        name='Oddiy zona',
        defaults={
            'description': '3-4 kishilik umumiy kutish joyi',
            'price': 0,
            'icon': '🆓'
        }
    )
    Zone.objects.get_or_create(
        name='VIP zona',
        defaults={
            'description': 'Alohida qulay zona',
            'price': 150000,
            'icon': '👑'
        }
    )
    print("Zones populated successfully.")

if __name__ == '__main__':
    setup_zones()
