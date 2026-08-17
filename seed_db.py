import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from barber.models import Barber, Service

def seed():
    # Create Barbers if not exist
    barbers_data = [
        {
            "name": "Aziz Usta",
            "specialty": "10 yillik tajriba / Bosh sartarosh",
            "rating": 4.9,
            "photo_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=150&auto=format&fit=crop"
        },
        {
            "name": "Jahongir Rustamov",
            "specialty": "Top Barber / Royal Stylist",
            "rating": 4.9,
            "photo_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=150&auto=format&fit=crop"
        },
        {
            "name": "Sardor Alimov",
            "specialty": "Soch va Soqol mutaxassisi",
            "rating": 4.8,
            "photo_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=150&auto=format&fit=crop"
        },
        {
            "name": "Diyorbek Toshpo'latov",
            "specialty": "Beard & Styling Master",
            "rating": 5.0,
            "photo_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?q=80&w=150&auto=format&fit=crop"
        }
    ]
    for b in barbers_data:
        Barber.objects.get_or_create(
            name=b["name"],
            defaults=b
        )
    print("Barbers populated.")

    # Create Services matching website
    services_data = [
        {"icon": "👑", "name": "Soch + Soqol (VIP)", "price": 80000, "duration_minutes": 60},
        {"icon": "✂️", "name": "Klassik soch olish", "price": 50000, "duration_minutes": 30},
        {"icon": "🧔", "name": "Soqol dizayni", "price": 40000, "duration_minutes": 25},
        {"icon": "✨", "name": "Royal Premium Pack (Soch + Soqol + Mask)", "price": 120000, "duration_minutes": 60},
    ]
    for s in services_data:
        Service.objects.get_or_create(
            name=s["name"],
            defaults=s
        )
    print("Services populated.")

if __name__ == '__main__':
    seed()
