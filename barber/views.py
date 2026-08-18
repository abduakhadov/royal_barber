from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import Customer, Barber, Service, Booking, Zone
import json
import datetime
import requests
import logging

logger = logging.getLogger(__name__)

def index(request):
    external_url = getattr(settings, 'EXTERNAL_WEBSITE_URL', 'https://hackaton-eood.onrender.com/')
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
    if not Service.objects.exists():
        default_services = [
            {"icon": "✂️", "name": "Klassik soch olish", "price": 50000, "duration_minutes": 30},
            {"icon": "🧔", "name": "Soqol dizayni", "price": 40000, "duration_minutes": 25},
            {"icon": "👑", "name": "Soch + Soqol (VIP)", "price": 80000, "duration_minutes": 60},
        ]
        for s in default_services:
            Service.objects.get_or_create(name=s["name"], defaults=s)

    services = Service.objects.all().order_by('id')
    data = [{
        'id': s.id,
        'name': s.name,
        'price': float(s.price),
        'duration_minutes': s.duration_minutes,
        'icon': s.icon
    } for s in services]
    return JsonResponse({'services': data})

def get_barbers(request):
    if not Barber.objects.exists():
        default_barbers = [
            {"name": "Aziz Usta", "specialty": "10 yillik tajriba / Bosh sartarosh (9:00 - 19:00)", "rating": 4.9, "photo_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=250&auto=format&fit=crop"},
        ]
        for b in default_barbers:
            Barber.objects.get_or_create(name=b["name"], defaults=b)

    barbers = Barber.objects.all().order_by('id')

    data = [{
        'id': b.id,
        'name': b.name,
        'photo_url': b.photo_url,
        'rating': b.rating,
        'specialty': b.specialty
    } for b in barbers]
    return JsonResponse({'barbers': data})

def get_available_slots(request):
    barber_id = request.GET.get('barber_id')
    date_str = request.GET.get('date')
    zone_id = request.GET.get('zone_id')
    service_id = request.GET.get('service_id')
    
    if not all([barber_id, date_str, service_id]):
        return JsonResponse({'error': "Hamma ma'lumotlar kiritilishi shart."}, status=400)
        
    date = parse_date(date_str)
    if not date:
        return JsonResponse({'error': "Sana formati noto'g'ri."}, status=400)
        
    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return JsonResponse({'error': "Xizmat topilmadi."}, status=404)

    # 15 daqiqadan oshgan to'lanmagan pending navbatlarni bekor qilish
    expire_threshold = timezone.now() - datetime.timedelta(minutes=15)
    Booking.objects.filter(
        status='pending',
        is_paid=False,
        created_at__lt=expire_threshold
    ).update(status='cancelled')

    # Ish vaqti (Dushanba=0, Shanba=5, Yakshanba=6)
    weekday = date.weekday()
    if weekday == 6: # Yakshanba
        return JsonResponse({'slots': [], 'closed': True})
    elif weekday == 5: # Shanba
        start_hour, end_hour = 10, 22
    else: # Dushanba-Juma
        start_hour, end_hour = 9, 21

    start_time = datetime.datetime.combine(date, datetime.time(start_hour, 0))
    day_end_time = datetime.datetime.combine(date, datetime.time(end_hour, 0))
    
    now = timezone.now().astimezone(datetime.timezone(datetime.timedelta(hours=5)))
    is_today = (date == now.date())

    all_slots = []
    current_time = start_time
    
    while current_time < day_end_time:
        slot_start_dt = current_time
        slot_end_dt = slot_start_dt + datetime.timedelta(minutes=service.duration_minutes)
        
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
        
        # O'tgan vaqt tekshiruvi
        if is_today and slot_start_dt.time() <= now.time():
            slot_info['available'] = False
            slot_info['reason'] = 'past'
            all_slots.append(slot_info)
            current_time += datetime.timedelta(minutes=30)
            continue
            
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
            
        # Zona bandligini tekshirish
        if zone_id:
            try:
                zone = Zone.objects.get(id=zone_id)
                zone_overlapping_count = Booking.objects.filter(
                    zone_id=zone_id,
                    date=date,
                    status__in=active_status
                ).filter(overlap_q).count()
                
                if zone_overlapping_count >= zone.capacity:
                    slot_info['available'] = False
                    slot_info['reason'] = 'zone_full'
            except Zone.DoesNotExist:
                pass
            
        all_slots.append(slot_info)
        current_time += datetime.timedelta(minutes=30)
        
    return JsonResponse({'slots': all_slots, 'closed': False})

@csrf_exempt
def book_appointment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Faqat POST so\'rovi qabul qilinadi.'}, status=405)
        
    try:
        data = json.loads(request.body)
        tg_id_raw = data.get('telegram_id')
        first_name = data.get('first_name') or 'Mijoz'
        last_name = data.get('last_name') or ''
        username = data.get('username') or ''
        phone = data.get('phone') or ''
        
        zone_id = data.get('zone_id')
        barber_id = data.get('barber_id')
        service_id = data.get('service_id')
        date_str = data.get('date')
        time_slot_str = data.get('time_slot')

        if not all([barber_id, service_id, date_str, time_slot_str]):
            return JsonResponse({'error': 'Hamma ma\'lumotlar to\'ldirilishi shart.'}, status=400)
            
        date = parse_date(date_str)
        time_slot = datetime.datetime.strptime(time_slot_str, '%H:%M').time()
        
        # Telegram ID ni xavfsiz son formatga o'tkazish
        try:
            tg_id = int(tg_id_raw) if tg_id_raw else 123456
        except (ValueError, TypeError):
            tg_id = 123456

        with transaction.atomic():
            zone = Zone.objects.filter(id=zone_id).first() if zone_id else None
            barber = Barber.objects.get(id=barber_id)
            service = Service.objects.get(id=service_id)
            
            # Double-booking tekshiruvi backendda
            slot_start_dt = datetime.datetime.combine(date, time_slot)
            slot_end_dt = slot_start_dt + datetime.timedelta(minutes=service.duration_minutes)
            slot_end_time = slot_end_dt.time()
            
            overlap_q = Q(time_slot__lt=slot_end_time) & Q(end_time__gt=time_slot)
            active_status = ['pending', 'confirmed']
            
            if Booking.objects.filter(barber=barber, date=date, status__in=active_status).filter(overlap_q).exists():
                return JsonResponse({'error': 'Ushbu vaqt boshqa mijoz tomonidan band qilindi. Iltimos, boshqa vaqt tanlang.'}, status=400)
                
            if zone and Booking.objects.filter(zone=zone, date=date, status__in=active_status).filter(overlap_q).count() >= zone.capacity:
                return JsonResponse({'error': 'Ushbu vaqtda zona to\'lgan. Boshqa vaqt tanlang.'}, status=400)
                
            # Customer ni olish yoki yangilash
            customer, _ = Customer.objects.get_or_create(
                telegram_id=tg_id,
                defaults={'first_name': first_name, 'last_name': last_name, 'username': username, 'phone': phone}
            )
            if first_name and customer.first_name != first_name:
                customer.first_name = first_name
            if phone and customer.phone != phone:
                customer.phone = phone
            if username and customer.username != username:
                customer.username = username
            customer.save()
            
            booking = Booking.objects.create(
                customer=customer,
                zone=zone,
                barber=barber,
                service=service,
                date=date,
                time_slot=time_slot,
                status='confirmed'
            )
            
            booking_code = f"RB-{booking.id:04d}"
            
            # Telegram bot orqali xabar yuborish
            bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
            if bot_token and customer.telegram_id and customer.telegram_id != 123456:
                total_price = int(service.price) + (int(zone.price) if zone else 0)
                lang = data.get('lang', 'uz')
                price_str = f"{total_price:,} " + ("so'm" if lang == 'uz' else "сум" if lang == 'ru' else "UZS")

                if lang == 'ru':
                    text = (
                        f"👑 <b>ROYAL BARBER | Запись подтверждена!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎟 <b>Код бронирования:</b> <code>{booking_code}</code>\n\n"
                        f"📅 <b>Дата:</b> {booking.date}\n"
                        f"🕐 <b>Время:</b> {booking.time_slot.strftime('%H:%M')}\n"
                        f"👨‍🎨 <b>Мастер:</b> {booking.barber.name}\n"
                        f"✂️ <b>Услуга:</b> {booking.service.name}\n"
                        f"💰 <b>К оплате:</b> {price_str}\n\n"
                        f"📍 <i>Ташкент | Тел: +998 90 123 45 67</i>"
                    )
                elif lang == 'en':
                    text = (
                        f"👑 <b>ROYAL BARBER | Appointment Confirmed!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎟 <b>Booking Code:</b> <code>{booking_code}</code>\n\n"
                        f"📅 <b>Date:</b> {booking.date}\n"
                        f"🕐 <b>Time:</b> {booking.time_slot.strftime('%H:%M')}\n"
                        f"👨‍🎨 <b>Barber:</b> {booking.barber.name}\n"
                        f"✂️ <b>Service:</b> {booking.service.name}\n"
                        f"💰 <b>Total Price:</b> {price_str}\n\n"
                        f"📍 <i>Tashkent | Phone: +998 90 123 45 67</i>"
                    )
                else:
                    text = (
                        f"👑 <b>ROYAL BARBER | Navbatingiz tasdiqlandi!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎟 <b>Bron kodingiz:</b> <code>{booking_code}</code>\n\n"
                        f"📅 <b>Sana:</b> {booking.date}\n"
                        f"🕐 <b>Vaqt:</b> {booking.time_slot.strftime('%H:%M')}\n"
                        f"👨‍🎨 <b>Usta:</b> {booking.barber.name}\n"
                        f"✂️ <b>Xizmat:</b> {booking.service.name}\n"
                        f"💰 <b>Narx:</b> <b>{price_str}</b>\n\n"
                        f"📍 <i>Toshkent shahri | Tel: +998 90 123 45 67</i>"
                    )
                
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                try:
                    requests.post(url, json={'chat_id': customer.telegram_id, 'text': text, 'parse_mode': 'HTML'}, timeout=4)
                except Exception as e:
                    logger.error(f"Telegram notification error: {e}")
            
        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
            'booking_code': booking_code,
            'barber_name': barber.name,
            'service_name': service.name,
            'date': str(booking.date),
            'time_slot': booking.time_slot.strftime('%H:%M'),
            'price': float(service.price + (zone.price if zone else 0)),
            'message': 'Navbatingiz muvaffaqiyatli tasdiqlandi!'
        })
        
    except (json.JSONDecodeError, Barber.DoesNotExist, Service.DoesNotExist) as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Booking error: {e}")
        return JsonResponse({'error': f"Xatolik yuz berdi: {str(e)}"}, status=500)

def get_my_bookings(request):
    tg_id = request.GET.get('telegram_id')
    phone = request.GET.get('phone')
    
    query = Q()
    if tg_id and tg_id != '123456':
        try:
            query |= Q(customer__telegram_id=int(tg_id))
        except ValueError:
            pass
    if phone:
        query |= Q(customer__phone__icontains=phone)
        
    if not query:
        return JsonResponse({'bookings': []})
        
    bookings = Booking.objects.filter(query).order_by('-date', '-time_slot')[:10]
    data = [{
        'id': b.id,
        'booking_code': f"RB-{b.id:04d}",
        'barber_name': b.barber.name,
        'service_name': b.service.name,
        'date': str(b.date),
        'time_slot': b.time_slot.strftime('%H:%M'),
        'total_price': float(b.service.price + (b.zone.price if b.zone else 0)),
        'status': b.status,
        'is_paid': b.is_paid,
    } for b in bookings]
    return JsonResponse({'bookings': data})

@csrf_exempt
def cancel_booking_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST talab qilinadi'}, status=405)
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        booking = Booking.objects.get(id=booking_id)
        booking.status = 'cancelled'
        booking.save()
        return JsonResponse({'success': True, 'message': 'Navbat bekor qilindi.'})
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Navbat topilmadi.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
