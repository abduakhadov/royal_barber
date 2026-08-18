import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from barber.models import Barber, Service, Zone

def seed():
    # 1. Create Zones
    zones_data = [
        {"name": "Oddiy zona", "description": "Umumiy shinam kutish zali", "price": 0, "icon": "🪑", "type": "ordinary", "capacity": 5},
        {"name": "VIP zona", "description": "Alohida qulay xona va maxsus xizmat", "price": 50000, "icon": "👑", "type": "vip", "capacity": 2},
    ]
    for z in zones_data:
        Zone.objects.get_or_create(name=z["name"], defaults=z)
    print("[+] Zonalar yangilandi.")

    # 2. Create Barbers
    barbers_data = [
        {
            "name": "Aziz Usta",
            "specialty": "10 yillik tajriba / Bosh sartarosh",
            "rating": 4.9,
            "photo_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=250&auto=format&fit=crop"
        },
        {
            "name": "Jahongir Rustamov",
            "specialty": "Top Barber / Royal Stylist",
            "rating": 4.9,
            "photo_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=250&auto=format&fit=crop"
        },
        {
            "name": "Sardor Alimov",
            "specialty": "Soch va Soqol mutaxassisi",
            "rating": 4.8,
            "photo_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=250&auto=format&fit=crop"
        },
        {
            "name": "Diyorbek Toshpo'latov",
            "specialty": "Beard & Styling Master",
            "rating": 5.0,
            "photo_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?q=80&w=250&auto=format&fit=crop"
        }
    ]
    for b in barbers_data:
        Barber.objects.update_or_create(
            name=b["name"],
            defaults=b
        )
    print("[+] Ustalar ro'yxati yangilandi.")

    # 3. Create Services matching website
    services_data = [
        {"icon": "👑", "name": "Soch + Soqol (VIP)", "price": 80000, "duration_minutes": 60},
        {"icon": "✂️", "name": "Klassik soch olish", "price": 50000, "duration_minutes": 30},
        {"icon": "🧔", "name": "Soqol dizayni", "price": 40000, "duration_minutes": 25},
        {"icon": "✨", "name": "Royal Premium Pack (Soch + Soqol + Mask)", "price": 120000, "duration_minutes": 60},
        {"icon": "👦", "name": "Bolalar soch turmagi", "price": 35000, "duration_minutes": 25},
        {"icon": "💆‍♂️", "name": "Yuz parvarishi va qora niqob", "price": 30000, "duration_minutes": 20},
    ]
    for s in services_data:
        Service.objects.update_or_create(
            name=s["name"],
            defaults=s
        )
    print("[+] Xizmatlar ro'yxati yangilandi.")

if __name__ == '__main__':
    seed()

