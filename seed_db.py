import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from barber.models import Barber, Service

def seed():
    # Clear existing to prevent duplicates
    Barber.objects.all().delete()
    Service.objects.all().delete()

    # Create Barbers
    barbers = [
        {
            "name": "Jahongir Rustamov",
            "specialty": "Top Barber / Royal Stylist",
            "rating": 4.9,
            "photo_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=150&auto=format&fit=crop"
        },
        {
            "name": "Sardor Alimov",
            "specialty": "Soch va Soqol mutaxassisi",
            "rating": 4.8,
            "photo_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=150&auto=format&fit=crop"
        },
        {
            "name": "Diyorbek Toshpo'latov",
            "specialty": "Beard & Styling Master",
            "rating": 5.0,
            "photo_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=150&auto=format&fit=crop"
        }
    ]
    for b in barbers:
        Barber.objects.create(**b)
    print("Barbers created.")

    # Create Services
    services = [
        {"icon": "✂️", "name": "Soch kesish (Classic)", "price": 60000, "duration_minutes": 30},
        {"icon": "🧔", "name": "Soqol shakllantirish (Beard styling)", "price": 40000, "duration_minutes": 25},
        {"icon": "✨", "name": "Royal Premium Pack (Soch + Soqol + Mask)", "price": 120000, "duration_minutes": 60},
        {"icon": "💆‍♂️", "name": "Bosh massaji va Yuvish", "price": 30000, "duration_minutes": 20},
    ]
    for s in services:
        Service.objects.create(**s)
    print("Services created.")

if __name__ == '__main__':
    seed()
