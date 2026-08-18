import os
import sys
import html
import logging
import datetime
import telebot
from telebot import types
from django.conf import settings
import django

# Setup django if running standalone
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()

from barber.models import Customer, Booking, Barber, Service, Zone
from django.utils import timezone
from django.db.models import Q

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = getattr(settings, 'TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN) if TOKEN != 'YOUR_BOT_TOKEN' else None

# In-memory temporary state for bot-based booking wizard
# Structure: user_id -> {'service_id': 1, 'barber_id': 2, 'date': '2026-08-20', 'time': '14:00'}
user_booking_state = {}

def get_main_menu():
    web_app_url = getattr(settings, 'MINI_APP_URL', 'http://127.0.0.1:8000/').strip()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if web_app_url.startswith('https://'):
        btn_app = types.KeyboardButton("💈 Mini Appda bron qilish", web_app=types.WebAppInfo(url=web_app_url))
        btn_book = types.KeyboardButton("✂️ Botda tezkor navbat")
        markup.add(btn_app, btn_book)
    else:
        btn_book = types.KeyboardButton("💈 Navbat olish")
        markup.add(btn_book)
        
    btn_services = types.KeyboardButton("✂️ Xizmatlar")
    btn_barbers = types.KeyboardButton("👨‍🎨 Ustalar")
    btn_bookings = types.KeyboardButton("📋 Mening navbatim")
    btn_payment = types.KeyboardButton("💳 To‘lov")
    btn_about = types.KeyboardButton("ℹ️ Biz haqimizda")
    btn_website = types.KeyboardButton("🌐 Rasmiy sayt")
    
    markup.add(btn_services, btn_barbers)
    markup.add(btn_bookings, btn_payment)
    markup.add(btn_about, btn_website)
    return markup

@bot.message_handler(commands=['start']) if bot else None
def handle_start(message):
    try:
        tg_id = message.from_user.id
        first_name = message.from_user.first_name or "Mijoz"
        last_name = message.from_user.last_name or ""
        username = message.from_user.username or ""
        
        customer, created = Customer.objects.get_or_create(
            telegram_id=tg_id,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'username': username
            }
        )
        
        if customer.phone:
            send_welcome(message.chat.id, first_name)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            btn_phone = types.KeyboardButton("📱 Telefon raqamni ulashish", request_contact=True)
            markup.add(btn_phone)
            
            welcome_auth = (
                f"👑 <b>ROYAL BARBER</b> — <i>STYLE IS KING</i>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👋 Salom, <b>{html.escape(first_name)}</b>!\n\n"
                f"💈 <b>Royal Barber</b> premium sartaroshxonasining rasmiy botiga xush kelibsiz.\n\n"
                f"🔐 Qulay va tez navbat olish uchun telefon raqamingizni tasdiqlang:"
            )
            bot.send_message(
                message.chat.id,
                welcome_auth,
                parse_mode="HTML",
                reply_markup=markup
            )
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@bot.message_handler(content_types=['contact']) if bot else None
def handle_contact(message):
    try:
        if message.contact and message.contact.user_id == message.from_user.id:
            phone = message.contact.phone_number
            tg_id = message.from_user.id
            first_name = message.from_user.first_name or "Mijoz"
            
            customer, _ = Customer.objects.get_or_create(
                telegram_id=tg_id,
                defaults={'first_name': first_name}
            )
            customer.phone = phone
            customer.save()
            
            bot.send_message(
                message.chat.id,
                f"✅ Rahmat! Raqamingiz muvaffaqiyatli saqlandi: <b>{phone}</b>",
                parse_mode="HTML"
            )
            send_welcome(message.chat.id, first_name)
        else:
            bot.send_message(message.chat.id, "⚠️ Iltimos, pastdagi tugma orqali o'zingizning raqamingizni yuboring.")
    except Exception as e:
        logger.error(f"Error in handle_contact: {e}")

def send_welcome(chat_id, first_name):
    """Sayt uslubidagi asosiy xush kelibsiz xabari."""
    web_app_url = getattr(settings, 'MINI_APP_URL', 'https://royal-barber.onrender.com/').strip()
    website_url = getattr(settings, 'EXTERNAL_WEBSITE_URL', 'https://hackaton-eood.onrender.com/').strip()
    
    welcome_text = (
        f"👑 <b>ROYAL BARBER</b> — <i>STYLE IS KING</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Xush kelibsiz, <b>{html.escape(first_name)}</b>!\n\n"
        f"💈 <b>Professional ustalar, sifatli xizmat va qulay onlayn bron tizimi</b> — barchasi bir joyda.\n\n"
        f"✨ <i>O'zingizga qulay vaqtni tanlang va professional ustalarimiz xizmatidan bahramand bo'ling!</i>\n\n"
        f"👇 Quyidagi menyudan foydalaning yoki to'g'ridan-to'g'ri <b>Mini App</b>ni oching:"
    )
    
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    if web_app_url.startswith('https://'):
        inline_kb.add(types.InlineKeyboardButton("🚀 Mini Appda bron qilish", web_app=types.WebAppInfo(url=web_app_url)))
    inline_kb.add(types.InlineKeyboardButton("✂️ Bot ichida navbat olish", callback_data="bot_book_start"))
    if website_url:
        inline_kb.add(types.InlineKeyboardButton("🌐 Rasmiy veb-saytimiz", url=website_url))
        
    bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=get_main_menu())
    bot.send_message(chat_id, "⚡️ <b>Tezkor harakatlar:</b>", parse_mode="HTML", reply_markup=inline_kb)

@bot.message_handler(commands=['help']) if bot else None
def handle_help(message):
    help_text = (
        "👑 <b>ROYAL BARBER | Yordam</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>Mavjud buyruqlar:</b>\n\n"
        "• /start — Botni ishga tushirish\n"
        "• /book — Onlayn navbat olish\n"
        "• /services — Bizning xizmatlar va narxlar\n"
        "• /barbers — Professional ustalarimiz\n"
        "• /bookings — Sizning faol navbatlaringiz\n"
        "• /pay — To'lovlar bo'limi\n"
        "• /check [kod] — Bron kodini tekshirish (Masalan: <code>/check RB-0012</code>)\n"
        "• /about — Manzil va aloqa ma'lumotlari\n"
        "• /help — Ushbu yordam oynasi"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="HTML")

@bot.message_handler(commands=['about']) if bot else None
@bot.message_handler(func=lambda m: m.text == "ℹ️ Biz haqimizda") if bot else None
def handle_about(message):
    website_url = getattr(settings, 'EXTERNAL_WEBSITE_URL', 'https://hackaton-eood.onrender.com/').strip()
    web_app_url = getattr(settings, 'MINI_APP_URL', 'https://royal-barber.onrender.com/').strip()
    
    about_text = (
        "👑 <b>ROYAL BARBER</b> — <i>STYLE IS KING</i>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💈 <b>Premium Sartaroshxona</b>\n"
        "Professional ustalar, zamonaviy uslub va oliy darajadagi servis.\n\n"
        "📍 <b>Manzil:</b> Toshkent shahri\n"
        "📞 <b>Telefon:</b> +998 (90) 123-45-67\n"
        "🕒 <b>Ish vaqti:</b> Har kuni 09:00 — 21:00 (Shanba 10:00 — 22:00, Yakshanba dam)\n\n"
        "✂️ Har bir xizmat yuqori sifat va e'tibor bilan bajariladi."
    )
    markup = types.InlineKeyboardMarkup()
    if website_url:
        markup.add(types.InlineKeyboardButton("🌐 Rasmiy sayt", url=website_url))
    if web_app_url.startswith('https://'):
        markup.add(types.InlineKeyboardButton("💈 Bron qilish", web_app=types.WebAppInfo(url=web_app_url)))
    else:
        markup.add(types.InlineKeyboardButton("💈 Botda navbat olish", callback_data="bot_book_start"))
        
    bot.send_message(message.chat.id, about_text, parse_mode="HTML", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🌐 Rasmiy sayt") if bot else None
def handle_website_btn(message):
    website_url = getattr(settings, 'EXTERNAL_WEBSITE_URL', 'https://hackaton-eood.onrender.com/').strip()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 Saytga o'tish", url=website_url))
    bot.send_message(
        message.chat.id, 
        f"👑 <b>Royal Barber Rasmiy Sayti</b>\n\nBarcha xizmatlar, fotogalereya va yangiliklar saytimizda:", 
        parse_mode="HTML", 
        reply_markup=markup
    )

# --- IN-BOT BOOKING WIZARD ---
@bot.message_handler(commands=['book']) if bot else None
@bot.message_handler(func=lambda m: m.text in ["💈 Navbat olish", "✂️ Botda tezkor navbat", "💈 Mini Appda bron qilish"]) if bot else None
def start_booking_flow(message):
    web_app_url = getattr(settings, 'MINI_APP_URL', '').strip()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    if web_app_url.startswith('https://'):
        markup.add(types.InlineKeyboardButton("🚀 Mini Appda qulay bron qilish", web_app=types.WebAppInfo(url=web_app_url)))
    markup.add(types.InlineKeyboardButton("✂️ Botda 1-bosqich: Xizmatni tanlash", callback_data="bot_book_start"))
    
    bot.send_message(
        message.chat.id,
        "👑 <b>ROYAL BARBER | Navbat olish</b>\n\nQaysi usulda navbat olmoqchisiz?",
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "bot_book_start") if bot else None
def step1_select_service(call):
    user_id = call.from_user.id
    user_booking_state[user_id] = {}
    
    services = Service.objects.all().order_by('id')
    if not services.exists():
        bot.answer_callback_query(call.id, "Xizmatlar mavjud emas.")
        return
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    for s in services:
        markup.add(types.InlineKeyboardButton(f"{s.icon} {s.name} — {int(s.price):,} so'm", callback_data=f"b_srv_{s.id}"))
        
    bot.edit_message_text(
        "✂️ <b>1-bosqich: Kerakli xizmatni tanlang:</b>",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("b_srv_")) if bot else None
def step2_select_barber(call):
    service_id = int(call.data.split("_")[2])
    user_id = call.from_user.id
    if user_id not in user_booking_state:
        user_booking_state[user_id] = {}
    user_booking_state[user_id]['service_id'] = service_id
    
    barbers = Barber.objects.all().order_by('id')
    markup = types.InlineKeyboardMarkup(row_width=1)
    for b in barbers:
        markup.add(types.InlineKeyboardButton(f"👨‍🎨 {b.name} (★ {b.rating})", callback_data=f"b_brb_{b.id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="bot_book_start"))
    
    service = Service.objects.filter(id=service_id).first()
    srv_name = service.name if service else ""
    
    bot.edit_message_text(
        f"✂️ Tanlangan xizmat: <b>{srv_name}</b>\n\n👨‍🎨 <b>2-bosqich: Sartarosh ustangizni tanlang:</b>",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("b_brb_")) if bot else None
def step3_select_date(call):
    barber_id = int(call.data.split("_")[2])
    user_id = call.from_user.id
    if user_id not in user_booking_state:
        user_booking_state[user_id] = {}
    user_booking_state[user_id]['barber_id'] = barber_id
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    today = timezone.now().astimezone(datetime.timezone(datetime.timedelta(hours=5))).date()
    days_uz = ["Dush", "Sesh", "Chor", "Pay", "Jum", "Shan", "Yak"]
    
    btn_list = []
    for i in range(7):
        d = today + datetime.timedelta(days=i)
        if d.weekday() == 6: # Yakshanba
            continue
        d_str = d.strftime('%Y-%m-%d')
        btn_text = f"📅 {d.day}-{d.strftime('%b')} ({days_uz[d.weekday()]})"
        btn_list.append(types.InlineKeyboardButton(btn_text, callback_data=f"b_date_{d_str}"))
        
    for i in range(0, len(btn_list), 2):
        if i + 1 < len(btn_list):
            markup.add(btn_list[i], btn_list[i+1])
        else:
            markup.add(btn_list[i])
            
    markup.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data=f"b_srv_{user_booking_state[user_id].get('service_id', 1)}"))
    
    barber = Barber.objects.filter(id=barber_id).first()
    b_name = barber.name if barber else ""
    
    bot.edit_message_text(
        f"👨‍🎨 Tanlangan usta: <b>{b_name}</b>\n\n📅 <b>3-bosqich: Qulay sanani tanlang:</b>",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("b_date_")) if bot else None
def step4_select_time(call):
    date_str = call.data.replace("b_date_", "")
    user_id = call.from_user.id
    if user_id not in user_booking_state:
        user_booking_state[user_id] = {}
    user_booking_state[user_id]['date'] = date_str
    
    service_id = user_booking_state[user_id].get('service_id')
    barber_id = user_booking_state[user_id].get('barber_id')
    
    try:
        service = Service.objects.get(id=service_id)
        barber = Barber.objects.get(id=barber_id)
        booking_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception as e:
        bot.answer_callback_query(call.id, "Ma'lumotlar eskirgan, qaytadan boshlang.")
        step1_select_service(call)
        return
        
    weekday = booking_date.weekday()
    start_hour, end_hour = (10, 22) if weekday == 5 else (9, 21)
    
    start_time = datetime.datetime.combine(booking_date, datetime.time(start_hour, 0))
    day_end_time = datetime.datetime.combine(booking_date, datetime.time(end_hour, 0))
    now = timezone.now().astimezone(datetime.timezone(datetime.timedelta(hours=5)))
    is_today = (booking_date == now.date())
    
    current_time = start_time
    available_slots = []
    
    while current_time < day_end_time:
        slot_start = current_time
        slot_end = slot_start + datetime.timedelta(minutes=service.duration_minutes)
        if slot_end > day_end_time:
            break
            
        slot_str = slot_start.strftime('%H:%M')
        if not (is_today and slot_start.time() <= now.time()):
            overlap_q = Q(time_slot__lt=slot_end.time()) & Q(end_time__gt=slot_start.time())
            is_booked = Booking.objects.filter(barber=barber, date=booking_date, status__in=['pending', 'confirmed']).filter(overlap_q).exists()
            if not is_booked:
                available_slots.append(slot_str)
        current_time += datetime.timedelta(minutes=30)
        
    markup = types.InlineKeyboardMarkup(row_width=3)
    if available_slots:
        time_btns = [types.InlineKeyboardButton(f"🕐 {t}", callback_data=f"b_time_{t}") for t in available_slots]
        for i in range(0, len(time_btns), 3):
            markup.row(*time_btns[i:i+3])
    else:
        markup.add(types.InlineKeyboardButton("❌ Bo'sh vaqt topilmadi", callback_data="none"))
        
    markup.add(types.InlineKeyboardButton("⬅️ Boshqa sana tanlash", callback_data=f"b_brb_{barber_id}"))
    
    bot.edit_message_text(
        f"📅 Sana: <b>{date_str}</b>\n👨‍🎨 Usta: <b>{barber.name}</b>\n✂️ Xizmat: <b>{service.name}</b>\n\n🕐 <b>4-bosqich: Bo'sh vaqtni tanlang:</b>",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("b_time_")) if bot else None
def step5_confirm_booking(call):
    time_str = call.data.replace("b_time_", "")
    user_id = call.from_user.id
    state = user_booking_state.get(user_id, {})
    
    service_id = state.get('service_id')
    barber_id = state.get('barber_id')
    date_str = state.get('date')
    
    if not all([service_id, barber_id, date_str]):
        bot.answer_callback_query(call.id, "Ma'lumotlar to'liq emas, qaytadan boshlang.")
        step1_select_service(call)
        return
        
    try:
        service = Service.objects.get(id=service_id)
        barber = Barber.objects.get(id=barber_id)
        booking_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        time_slot = datetime.datetime.strptime(time_str, '%H:%M').time()
        
        tg_user = call.from_user
        customer, _ = Customer.objects.get_or_create(
            telegram_id=user_id,
            defaults={
                'first_name': tg_user.first_name or "Mijoz",
                'last_name': tg_user.last_name or "",
                'username': tg_user.username or ""
            }
        )
        
        # Double booking check
        slot_end_dt = datetime.datetime.combine(booking_date, time_slot) + datetime.timedelta(minutes=service.duration_minutes)
        overlap_q = Q(time_slot__lt=slot_end_dt.time()) & Q(end_time__gt=time_slot)
        if Booking.objects.filter(barber=barber, date=booking_date, status__in=['pending', 'confirmed']).filter(overlap_q).exists():
            bot.answer_callback_query(call.id, "Kechirasiz, ushbu vaqt allaqachon band qilindi!", show_alert=True)
            step4_select_time(call)
            return
            
        booking = Booking.objects.create(
            customer=customer,
            barber=barber,
            service=service,
            date=booking_date,
            time_slot=time_slot,
            status='confirmed'
        )
        
        booking_code = f"RB-{booking.id:04d}"
        
        success_text = (
            f"🎉 <b>NAVABAT MUVAFFAQIYATLI TASDIQLANDI!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎟 <b>Bron kodingiz:</b> <code>{booking_code}</code>\n\n"
            f"📅 <b>Sana:</b> {booking.date}\n"
            f"🕐 <b>Vaqt:</b> {booking.time_slot.strftime('%H:%M')}\n"
            f"👨‍🎨 <b>Sartarosh:</b> {barber.name}\n"
            f"✂️ <b>Xizmat:</b> {service.name} ({service.duration_minutes} daq)\n"
            f"💰 <b>Narxi:</b> <b>{int(service.price):,} so'm</b>\n\n"
            f"📍 <i>Toshkent shahri | Tel: +998 90 123 45 67</i>\n"
            f"Sizni kutamiz!"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Hozir to'lash", callback_data=f"pay_{booking.id}"))
        markup.add(types.InlineKeyboardButton("📋 Mening navbatlarim", callback_data="my_bookings_list"))
        
        bot.edit_message_text(
            success_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
        # Clear state
        user_booking_state.pop(user_id, None)
        
    except Exception as e:
        logger.error(f"Error creating booking in bot: {e}")
        bot.answer_callback_query(call.id, f"Xatolik: {e}", show_alert=True)

# --- SERVICES & BARBERS ---
@bot.message_handler(commands=['services']) if bot else None
@bot.message_handler(func=lambda m: m.text == "✂️ Xizmatlar") if bot else None
def show_services(message):
    services = Service.objects.all().order_by('id')
    if not services.exists():
        bot.send_message(message.chat.id, "Hozircha xizmatlar kiritilmagan.")
        return
        
    web_app_url = getattr(settings, 'MINI_APP_URL', '').strip()
    text = (
        "👑 <b>ROYAL BARBER | Xizmatlar va Narxlar</b>\n"
        "<i>Har bir xizmat yuqori sifat va e'tibor bilan bajariladi</i>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    for s in services:
        name = html.escape(s.name)
        text += f"{s.icon} <b>{name}</b>\n"
        text += f"💰 <b>{int(s.price):,} so'm</b>  |  ⏱ {s.duration_minutes} daqiqa\n\n"
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    if web_app_url.startswith('https://'):
        markup.add(types.InlineKeyboardButton("🚀 Mini Appda bron qilish", web_app=types.WebAppInfo(url=web_app_url)))
    markup.add(types.InlineKeyboardButton("💈 Botda navbat olish", callback_data="bot_book_start"))
    
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

@bot.message_handler(commands=['barbers']) if bot else None
@bot.message_handler(func=lambda m: m.text == "👨‍🎨 Ustalar") if bot else None
def show_barbers(message):
    barbers = Barber.objects.all().order_by('id')
    if not barbers.exists():
        bot.send_message(message.chat.id, "Hozircha ustalar kiritilmagan.")
        return
        
    text = (
        "👑 <b>ROYAL BARBER | Bizning Ustalar</b>\n"
        "<i>Tajribali va professional sartaroshlar jamoasi</i>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    for b in barbers:
        name = html.escape(b.name)
        spec = html.escape(b.specialty or "Professional usta")
        rating = float(b.rating) if b.rating else 5.0
        stars = "⭐️" * int(round(rating))
        text += f"💈 <b>{name}</b>\n"
        text += f"👔 Mutaxassislik: {spec}\n"
        text += f"★ Reyting: <b>{rating:.2f}</b> {stars}\n\n"
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💈 Ustani tanlab navbat olish", callback_data="bot_book_start"))
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

# --- BOOKINGS & CODE CHECK ---
@bot.message_handler(commands=['bookings']) if bot else None
@bot.message_handler(func=lambda m: m.text == "📋 Mening navbatim") if bot else None
def my_bookings(message):
    tg_id = message.from_user.id
    try:
        customer = Customer.objects.get(telegram_id=tg_id)
    except Customer.DoesNotExist:
        bot.send_message(message.chat.id, "Siz hali ro'yxatdan o'tmagansiz. /start buyrug'ini bosing.")
        return
        
    bookings = Booking.objects.filter(customer=customer).order_by('-date', '-time_slot')[:5]
    if not bookings.exists():
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💈 Hoziroq navbat olish", callback_data="bot_book_start"))
        bot.send_message(message.chat.id, "Sizda hali faol navbatlar yo'q. Navbat oling! 📅", reply_markup=markup)
        return
        
    bot.send_message(message.chat.id, "📋 <b>Sizning navbatlaringiz:</b>", parse_mode="HTML")
    
    for b in bookings:
        status_emoji = {
            'pending': '⏳ Kutilmoqda',
            'confirmed': '✅ Tasdiqlandi',
            'cancelled': '❌ Bekor qilindi',
            'completed': '🎉 Yakunlandi'
        }.get(b.status, b.status)
        
        b_name = html.escape(b.barber.name)
        s_name = html.escape(b.service.name)
        total_price = int(b.service.price) + (int(b.zone.price) if b.zone else 0)
        booking_code = f"RB-{b.id:04d}"
            
        text = (
            f"👑 <b>ROYAL BARBER | Navbat:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎟 <b>Bron kodi:</b> <code>{booking_code}</code>\n"
            f"📅 Sana: <b>{b.date}</b>\n"
            f"🕐 Vaqt: <b>{b.time_slot.strftime('%H:%M')}</b>\n"
            f"👨‍🎨 Usta: <b>{b_name}</b>\n"
            f"✂️ Xizmat: <b>{s_name}</b>\n"
            f"💰 Narxi: <b>{total_price:,} so'm</b>\n"
            f"Holati: {status_emoji}"
        )
        
        markup = types.InlineKeyboardMarkup()
        if b.status in ['pending', 'confirmed']:
            markup.add(types.InlineKeyboardButton("❌ Navbatni bekor qilish", callback_data=f"cancel_{b.id}"))
            if not b.is_paid:
                markup.add(types.InlineKeyboardButton("💳 Hozir to'lash", callback_data=f"pay_{b.id}"))
                
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "my_bookings_list") if bot else None
def callback_my_bookings(call):
    my_bookings(call.message)

@bot.message_handler(commands=['check']) if bot else None
def handle_check_code(message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Iltimos, kodni kiriting. Masalan: <code>/check RB-0001</code>", parse_mode="HTML")
        return
        
    code_raw = parts[1].upper().replace('#', '')
    # Extract ID
    try:
        if code_raw.startswith('RB-'):
            b_id = int(code_raw.replace('RB-', ''))
        else:
            b_id = int(code_raw)
            
        booking = Booking.objects.filter(id=b_id).first()
        if not booking:
            bot.send_message(message.chat.id, f"❌ <b>{code_raw}</b> kodli navbat topilmadi.", parse_mode="HTML")
            return
            
        status_text = {
            'pending': '⏳ Kutilmoqda',
            'confirmed': '✅ Tasdiqlangan',
            'cancelled': '❌ Bekor qilingan',
            'completed': '🎉 Yakunlangan'
        }.get(booking.status, booking.status)
        
        bot.send_message(
            message.chat.id,
            f"🎟 <b>Navbat ma'lumotlari:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Kod: <code>RB-{booking.id:04d}</code>\n"
            f"Mijoz: <b>{booking.customer.first_name}</b>\n"
            f"Sana: <b>{booking.date}</b> | <b>{booking.time_slot.strftime('%H:%M')}</b>\n"
            f"Usta: <b>{booking.barber.name}</b>\n"
            f"Xizmat: <b>{booking.service.name}</b>\n"
            f"Holat: <b>{status_text}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        bot.send_message(message.chat.id, "Kodni tekshirishda xatolik yuz berdi. To'g'ri format: RB-0001")

# --- PAYMENTS ---
@bot.message_handler(func=lambda m: m.text == "💳 To‘lov") if bot else None
def show_payments(message):
    tg_id = message.from_user.id
    try:
        customer = Customer.objects.get(telegram_id=tg_id)
    except Customer.DoesNotExist:
        bot.send_message(message.chat.id, "Ro'yxatdan o'tish uchun /start ni bosing.")
        return
        
    unpaid = Booking.objects.filter(customer=customer, is_paid=False, status__in=['pending', 'confirmed'])
    if not unpaid.exists():
        bot.send_message(message.chat.id, "Sizda to'lanishi kerak bo'lgan to'lanmagan navbatlar yo'q. 😊")
        return
        
    for b in unpaid:
        b_name = html.escape(b.barber.name)
        s_name = html.escape(b.service.name)
        total_price = int(b.service.price) + (int(b.zone.price) if b.zone else 0)
            
        text = (
            f"💳 <b>To'lov uchun navbat:</b>\n\n"
            f"🎟 Kod: <code>RB-{b.id:04d}</code>\n"
            f"Usta: {b_name}\n"
            f"Xizmat: {s_name}\n"
            f"Sana va Vaqt: {b.date} {b.time_slot.strftime('%H:%M')}\n"
            f"To'lov summasi: <b>{total_price:,} UZS</b>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"💳 To'lash ({total_price:,} UZS)", callback_data=f"pay_{b.id}"))
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_')) if bot else None
def handle_cancel_booking(call):
    booking_id = int(call.data.split('_')[1])
    try:
        booking = Booking.objects.get(id=booking_id)
        booking.status = 'cancelled'
        booking.save()
        bot.answer_callback_query(call.id, "Navbatingiz bekor qilindi.")
        bot.edit_message_text(
            f"❌ <b>Navbat bekor qilindi</b>\n\n🎟 Kod: <code>RB-{booking.id:04d}</code>\nSana: {booking.date}\nUsta: {booking.barber.name}\nXizmat: {booking.service.name}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )
    except Booking.DoesNotExist:
        bot.answer_callback_query(call.id, "Xatolik: Navbat topilmadi.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_')) if bot else None
def handle_pay_booking(call):
    booking_id = int(call.data.split('_')[1])
    try:
        booking = Booking.objects.get(id=booking_id)
        if booking.is_paid:
            bot.answer_callback_query(call.id, "Ushbu to'lov allaqachon amalga oshirilgan.", show_alert=True)
            return
            
        provider_token = getattr(settings, 'PAYMENT_PROVIDER_TOKEN', '').strip()
        if provider_token and not provider_token.startswith("398062629:TEST"):
            total_price = int(booking.service.price) + (int(booking.zone.price) if booking.zone else 0)
            price_tiyin = total_price * 100
            prices = [types.LabeledPrice(label=booking.service.name, amount=price_tiyin)]
            
            bot.send_invoice(
                chat_id=call.message.chat.id,
                title=f"Royal Barber: {booking.service.name}",
                description=f"Usta: {booking.barber.name} | Sana: {booking.date} {booking.time_slot.strftime('%H:%M')}",
                invoice_payload=f"booking_{booking.id}",
                provider_token=provider_token,
                currency="UZS",
                prices=prices,
                start_parameter=f"pay_{booking.id}"
            )
            bot.answer_callback_query(call.id, "To'lov cheki yuborildi!")
        else:
            booking.is_paid = True
            booking.save()
            bot.answer_callback_query(call.id, "To'lov muvaffaqiyatli tasdiqlandi! ✅", show_alert=True)
            bot.edit_message_text(
                f"💳 <b>To'lov muvaffaqiyatli qabul qilindi!</b>\n\n🎟 Kod: <code>RB-{booking.id:04d}</code>\nUsta: {booking.barber.name}\nXizmat: {booking.service.name}\nSana: {booking.date}\nHolat: ✅ To'landi",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
    except Booking.DoesNotExist:
        bot.answer_callback_query(call.id, "Xatolik: Navbat topilmadi.", show_alert=True)

@bot.pre_checkout_query_handler(func=lambda query: True) if bot else None
def process_pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment']) if bot else None
def process_successful_payment(message):
    payload = message.successful_payment.invoice_payload
    if payload.startswith("booking_"):
        booking_id = int(payload.split("_")[1])
        try:
            booking = Booking.objects.get(id=booking_id)
            booking.is_paid = True
            booking.payment_id = message.successful_payment.telegram_payment_charge_id
            booking.status = 'confirmed'
            booking.save()
            
            b_name = html.escape(booking.barber.name)
            s_name = html.escape(booking.service.name)
            bot.send_message(
                message.chat.id,
                f"🎉 <b>To'lov muvaffaqiyatli qabul qilindi!</b>\n\n"
                f"🎟 <b>Bron kodi:</b> <code>RB-{booking.id:04d}</code>\n"
                f"Usta: <b>{b_name}</b>\n"
                f"Xizmat: <b>{s_name}</b>\n"
                f"Sana: <b>{booking.date}</b> ({booking.time_slot.strftime('%H:%M')})\n\n"
                f"✅ Sizning navbatingiz to'liq tasdiqlandi. Sizni kutamiz!",
                parse_mode="HTML"
            )
        except Booking.DoesNotExist:
            bot.send_message(message.chat.id, "To'lov qabul qilindi, lekin navbat topilmadi.")

def start_polling():
    if bot:
        import time as _time
        logger.info("Starting Telegram Bot polling...")
        try:
            bot.delete_webhook(drop_pending_updates=True)
            bot.get_updates(offset=-1, timeout=1)
        except Exception as e:
            logger.warning(f"Webhook/Updates cleanup: {e}")
            
        _time.sleep(1)
        logger.info("Bot polling active.")
        bot.infinity_polling(timeout=20, long_polling_timeout=20)
    else:
        logger.warning("Bot token not configured, skipping polling.")

if __name__ == '__main__':
    start_polling()
