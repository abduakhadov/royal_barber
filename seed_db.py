import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from barber.models import Barber, Service, Zone, Booking

def seed():
    # 1. Exact Services from https://hackaton-eood.onrender.com/services/
    exact_services = [
        {
            "id": 1,
            "name": "Klassik soch olish",
            "price": 50000,
            "duration_minutes": 30,
            "icon": "✂️"
        },
        {
            "id": 2,
            "name": "Soqol dizayni",
            "price": 40000,
            "duration_minutes": 25,
            "icon": "🧔"
        },
        {
            "id": 3,
            "name": "Soch + Soqol (VIP)",
            "price": 80000,
            "duration_minutes": 60,
            "icon": "👑"
        },
    ]

    # Delete extraneous services not in exact list
    valid_service_names = [s["name"] for s in exact_services]
    Service.objects.exclude(name__in=valid_service_names).delete()

    for s in exact_services:
        Service.objects.update_or_create(
            name=s["name"],
            defaults={
                "price": s["price"],
                "duration_minutes": s["duration_minutes"],
                "icon": s["icon"]
            }
        )
    print(f"[+] Xizmatlar sayt bilan 1:1 sinxronlandi ({Service.objects.count()} ta xizmat).")

    # 2. Exact Barbers from https://hackaton-eood.onrender.com/barbers/
    exact_barbers = [
        {
            "id": 1,
            "name": "Aziz Usta",
            "specialty": "10 yillik tajriba / Bosh sartarosh (9:00 - 19:00)",
            "rating": 4.9,
            "photo_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=250&auto=format&fit=crop"
        }
    ]

    valid_barber_names = [b["name"] for b in exact_barbers]
    Barber.objects.exclude(name__in=valid_barber_names).delete()

    for b in exact_barbers:
        Barber.objects.update_or_create(
            name=b["name"],
            defaults={
                "specialty": b["specialty"],
                "rating": b["rating"],
                "photo_url": b["photo_url"]
            }
        )
    print(f"[+] Ustalar sayt bilan 1:1 sinxronlandi ({Barber.objects.count()} ta usta).")

    # 3. Zones
    Zone.objects.get_or_create(
        name="Oddiy zona",
        defaults={
            "description": "Umumiy shinam zal",
            "price": 0,
            "icon": "🪑",
            "type": "ordinary",
            "capacity": 5
        }
    )

if __name__ == '__main__':
    seed()


