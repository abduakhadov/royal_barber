from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from django.conf import settings
from .models import Customer, Barber, Service, Booking, Zone
import json
import datetime

def index(request):
    external_url = getattr(settings, 'EXTERNAL_WEBSITE_URL', '')
    return render(request, 'barber/booking_app.html', {'external_website_url': external_url})

def get_zones(request):
    zones = Zone.objects.filter(is_active=True)
    data = [{
        'id': z.id,
        'name': z.name,
        'description': z.description,
        'price': float(z.price),
        'icon': z.icon,
        'type': z.type,
        'capacity': z.capacity
    } for z in zones]
    return JsonResponse({'zones': data})

def get_services(request):
    services = Service.objects.all()
    data = [{
        'id': s.id,
        'name': s.name,
        'price': float(s.price),
        'duration_minutes': s.duration_minutes,
        'icon': s.icon
    } for s in services]
    return JsonResponse({'services': data})

def get_barbers(request):
    barbers = Barber.objects.all()
    data = [{
        'id': b.id,
        'name': b.name,
        'photo_url': b.photo_url,
        'rating': b.rating,
        'specialty': b.specialty
    } for b in barbers]
    return JsonResponse({'barbers': data})

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

def get_available_slots(request):
    barber_id = request.GET.get('barber_id')
    date_str = request.GET.get('date')
    zone_id = request.GET.get('zone_id')
    service_id = request.GET.get('service_id')
    
    if not all([barber_id, date_str, zone_id, service_id]):
        return JsonResponse({'error': "Hamma ma'lumotlar kiritilishi shart."}, status=400)
        
    date = parse_date(date_str)
    if not date:
        return JsonResponse({'error': "Sana formati noto'g'ri."}, status=400)
        
    try:
        zone = Zone.objects.get(id=zone_id)
        service = Service.objects.get(id=service_id)
    except (Zone.DoesNotExist, Service.DoesNotExist):
        return JsonResponse({'error': "Zona yoki xizmat topilmadi."}, status=404)

    # 1. Tozalash: 15 daqiqadan oshgan to'lanmagan 'pending' navbatlarni bekor qilish
    expire_threshold = timezone.now() - datetime.timedelta(minutes=15)
    Booking.objects.filter(
        status='pending',
        is_paid=False,
        created_at__lt=expire_threshold
    ).update(status='cancelled')

    # Ish vaqtini aniqlash (Dushanba=0, Yakshanba=6)
    weekday = date.weekday()
    if weekday == 6: # Yakshanba
        return JsonResponse({'slots': [], 'closed': True})
    elif weekday == 5: # Shanba
        start_hour, end_hour = 10, 22
    else: # Dushanba-Juma
        start_hour, end_hour = 9, 21

    start_time = datetime.datetime.combine(date, datetime.time(start_hour, 0))
    day_end_time = datetime.datetime.combine(date, datetime.time(end_hour, 0))
    
    # Bugungi kun uchun o'tib ketgan vaqtni aniqlash
    # (Uzbekistan vaqti uchun UTC+5)
    now = timezone.now().astimezone(datetime.timezone(datetime.timedelta(hours=5)))
    is_today = (date == now.date())

    all_slots = []
    current_time = start_time
    
    while current_time < day_end_time:
        slot_start_dt = current_time
        slot_end_dt = slot_start_dt + datetime.timedelta(minutes=service.duration_minutes)
        
        # Agar xizmat ish vaqtidan chiqib ketsa, bu slotni qo'shmaymiz
        if slot_end_dt > day_end_time:
            break
            
        slot_time_str = slot_start_dt.strftime('%H:%M')
        slot_start_time = slot_start_dt.time()
        slot_end_time = slot_end_dt.time()
        
        slot_info = {
            'time': slot_time_str,
            'available': True,
            'reason': ''
        }
        
        # O'tgan vaqtni tekshirish
        if is_today and slot_start_dt.time() <= now.time():
            slot_info['available'] = False
            slot_info['reason'] = 'past'
            all_slots.append(slot_info)
            current_time += datetime.timedelta(minutes=30)
            continue
            
        # Overlap (To'qnashuv) tekshirish: Boshlanish vaqti avvalgi xizmatning tugashidan oldin,
        # tugash vaqti avvalgi xizmatning boshlanishidan keyin bo'lsa - to'qnashuv.
        overlap_q = Q(time_slot__lt=slot_end_time) & Q(end_time__gt=slot_start_time)
        active_status = ['pending', 'confirmed']
        
        # Usta bandligini tekshirish
        barber_overlap = Booking.objects.filter(
            barber_id=barber_id,
            date=date,
            status__in=active_status
        ).filter(overlap_q).exists()
        
        if barber_overlap:
            slot_info['available'] = False
            slot_info['reason'] = 'barber_booked'
            all_slots.append(slot_info)
            current_time += datetime.timedelta(minutes=30)
            continue
            
        # Zona bandligini tekshirish (sig'imi bo'yicha)
        zone_overlapping_count = Booking.objects.filter(
            zone_id=zone_id,
            date=date,
            status__in=active_status
        ).filter(overlap_q).count()
        
        if zone_overlapping_count >= zone.capacity:
            slot_info['available'] = False
            slot_info['reason'] = 'zone_full'
            
        all_slots.append(slot_info)
        current_time += datetime.timedelta(minutes=30)
        
    return JsonResponse({'slots': all_slots, 'closed': False})

@csrf_exempt
def book_appointment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Faqat POST so\'rovi qabul qilinadi.'}, status=405)
        
    try:
        data = json.loads(request.body)
        tg_id = data.get('telegram_id')
        first_name = data.get('first_name', 'Mijoz')
        last_name = data.get('last_name', '')
        username = data.get('username', '')
        
        zone_id = data.get('zone_id')
        barber_id = data.get('barber_id')
        service_id = data.get('service_id')
        date_str = data.get('date')
        time_slot_str = data.get('time_slot')

        if not all([tg_id, zone_id, barber_id, service_id, date_str, time_slot_str]):
            return JsonResponse({'error': 'Hamma ma\'lumotlar to\'ldirilishi shart.'}, status=400)
            
        date = parse_date(date_str)
        time_slot = datetime.datetime.strptime(time_slot_str, '%H:%M').time()
        
        with transaction.atomic():
            # Get objects
            zone = Zone.objects.get(id=zone_id)
            barber = Barber.objects.get(id=barber_id)
            service = Service.objects.get(id=service_id)
            
            # Double-booking tekshiruvi backendda (locking bilamiz, lekin db lock o'rniga qat'iy query qilamiz)
            slot_start_dt = datetime.datetime.combine(date, time_slot)
            slot_end_dt = slot_start_dt + datetime.timedelta(minutes=service.duration_minutes)
            slot_end_time = slot_end_dt.time()
            
            overlap_q = Q(time_slot__lt=slot_end_time) & Q(end_time__gt=time_slot)
            active_status = ['pending', 'confirmed']
            
            # Usta bandmi?
            if Booking.objects.filter(barber=barber, date=date, status__in=active_status).filter(overlap_q).exists():
                return JsonResponse({'error': 'Ushbu vaqt boshqa mijoz tomonidan band qilindi. Boshqa vaqt tanlang.'}, status=400)
                
            # Zona to'lganmi?
            if Booking.objects.filter(zone=zone, date=date, status__in=active_status).filter(overlap_q).count() >= zone.capacity:
                return JsonResponse({'error': 'Ushbu vaqtda zona to\'lgan. Boshqa vaqt tanlang.'}, status=400)
                
            # Get or create customer
            customer, _ = Customer.objects.get_or_create(
                telegram_id=tg_id,
                defaults={'first_name': first_name, 'last_name': last_name, 'username': username}
            )
            
            booking_status = 'confirmed' if zone.type == 'ordinary' else 'pending'
            
            booking = Booking.objects.create(
                customer=customer,
                zone=zone,
                barber=barber,
                service=service,
                date=date,
                time_slot=time_slot,
                status=booking_status
            )
            
            # Xabar yuborish
            import requests
            bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
            if bot_token:
                total_price = service.price + zone.price
                lang = data.get('lang', 'uz')
                
                # Format price safely based on language
                if total_price == 0:
                    price_str = 'Bepul' if lang == 'uz' else 'Бесплатно' if lang == 'ru' else 'Free'
                else:
                    price_str = f"{int(total_price):,} " + ("so'm" if lang == 'uz' else "сум" if lang == 'ru' else "UZS")

                if lang == 'ru':
                    text = (
                        f"✅ <b>Ваша запись подтверждена!</b>\n\n"
                        f"📅 Дата: {booking.date}\n"
                        f"🕐 Время: {booking.time_slot.strftime('%H:%M')}\n"
                        f"✂️ Мастер: {booking.barber.name}\n"
                        f"👑 Зона: {booking.zone.name}\n\n"
                        f"💰 Цена: {price_str}"
                    )
                    pending_warn = "\n\n⚠️ <i>Пожалуйста, оплатите через бота. Неоплаченные записи будут отменены через 15 минут.</i>"
                elif lang == 'en':
                    text = (
                        f"✅ <b>Your appointment is confirmed!</b>\n\n"
                        f"📅 Date: {booking.date}\n"
                        f"🕐 Time: {booking.time_slot.strftime('%H:%M')}\n"
                        f"✂️ Barber: {booking.barber.name}\n"
                        f"👑 Zone: {booking.zone.name}\n\n"
                        f"💰 Price: {price_str}"
                    )
                    pending_warn = "\n\n⚠️ <i>Please complete the payment via the bot. Unpaid bookings will be cancelled in 15 minutes.</i>"
                else:
                    text = (
                        f"✅ <b>Navbatingiz tasdiqlandi!</b>\n\n"
                        f"📅 Sana: {booking.date}\n"
                        f"🕐 Vaqt: {booking.time_slot.strftime('%H:%M')}\n"
                        f"✂️ Usta: {booking.barber.name}\n"
                        f"👑 Zona: {booking.zone.name}\n\n"
                        f"💰 Narx: {price_str}"
                    )
                    pending_warn = "\n\n⚠️ <i>Iltimos, bot orqali to'lovni amalga oshiring. To'lanmagan navbatlar 15 daqiqadan so'ng bekor qilinadi.</i>"

                if booking_status == 'pending':
                    text += pending_warn
                
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                try:
                    requests.post(url, json={'chat_id': customer.telegram_id, 'text': text, 'parse_mode': 'HTML'}, timeout=2)
                except Exception as e:
                    print("Telegram xabar yuborishda xato:", e)
            
        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
            'message': 'Navbat muvaffaqiyatli band qilindi!'
        })
        
    except (json.JSONDecodeError, Zone.DoesNotExist, Barber.DoesNotExist, Service.DoesNotExist) as e:
        return JsonResponse({'error': str(e)}, status=400)

