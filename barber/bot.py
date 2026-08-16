import os
import sys
import html
import logging
import telebot
from telebot import types
from django.conf import settings
import django

# Setup django if running standalone
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()

from barber.models import Customer, Booking, Barber, Service

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = getattr(settings, 'TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN) if TOKEN != 'YOUR_BOT_TOKEN' else None

def get_main_keyboard():
    # As requested by the user, we no longer use a reply keyboard. 
    # The 'Open' Menu Button is the primary way to interact.
    return types.ReplyKeyboardRemove()

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
        
        # Agar telefon raqami bor bo'lsa — to'g'ridan-to'g'ri xush kelibsiz
        if customer.phone:
            send_welcome(message.chat.id, first_name)
        else:
            # Telefon raqamini so'raymiz
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            btn_phone = types.KeyboardButton("📱 Telefon raqamni ulashish", request_contact=True)
            markup.add(btn_phone)
            
            bot.send_message(
                message.chat.id,
                f"👋 Salom, <b>{first_name}</b>!\n\n"
                "💈 Men <b>Royal Barber</b> botiman.\n\n"
                "🔐 Tizimga kirish uchun telefon raqamingizni ulashing.\n\n"
                "⚠️ <i>Raqamingiz faqat navbat olish uchun ishlatiladi.</i>",
                parse_mode="HTML",
                reply_markup=markup
            )
    except Exception as e:
        logger.error(f"Error in start command: {e}")

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📅 Navbat olish")
    btn2 = types.KeyboardButton("✂️ Xizmatlar")
    btn3 = types.KeyboardButton("👨🔧 Ustalar")
    btn4 = types.KeyboardButton("📋 Mening navbatim")
    btn5 = types.KeyboardButton("💳 To‘lov")
    btn6 = types.KeyboardButton("ℹ️ Biz haqimizda")
    markup.add(btn1)
    markup.add(btn2, btn3)
    markup.add(btn4, btn5)
    markup.add(btn6)
    return markup

@bot.message_handler(content_types=['contact']) if bot else None
def handle_contact(message):
    try:
        if message.contact and message.contact.user_id == message.from_user.id:
            phone = message.contact.phone_number
            tg_id = message.from_user.id
            first_name = message.from_user.first_name or "Mijoz"
            
            # Telefon raqamini saqlash
            customer, _ = Customer.objects.get_or_create(
                telegram_id=tg_id,
                defaults={'first_name': first_name}
            )
            customer.phone = phone
            customer.save()
            
            bot.send_message(
                message.chat.id,
                f"✅ Rahmat! Raqamingiz saqlandi: <b>{phone}</b>",
                parse_mode="HTML"
            )
            
            # Xush kelibsiz xabarini yuboramiz
            send_welcome(message.chat.id, first_name)
        else:
            bot.send_message(message.chat.id, "⚠️ Iltimos, o'zingizning telefon raqamingizni ulashing.")
    except Exception as e:
        logger.error(f"Error in handle_contact: {e}")

def send_welcome(chat_id, first_name):
    """Asosiy xush kelibsiz xabari."""
    welcome_text = (
        f"👋 Salom, <b>{first_name}</b>!\n\n"
        "💈 <b>Royal Barber</b> botiga xush kelibsiz.\n\n"
        "👇 O'zingizga kerakli bo'limni tanlang yoki navbat olish uchun chap pastdagi <b>«Mini Ilova»</b> tugmasini bosing!"
    )
    bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=get_main_menu())

@bot.message_handler(commands=['help']) if bot else None
def handle_help(message):
    help_text = (
        "❓ <b>Yordam bo'limi</b>\n\n"
        "Quyidagi buyruqlardan foydalanishingiz mumkin:\n"
        "/start - Botni qayta ishga tushirish\n"
        "/services - Xizmatlar ro'yxati\n"
        "/barbers - Ustalar ro'yxati\n"
        "/bookings - Faol navbatlar\n"
        "/about - Sartaroshxona ma'lumotlari"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="HTML")

@bot.message_handler(commands=['about']) if bot else None
def handle_about(message):
    about_text = (
        "💈 <b>Royal Barber Shop</b>\n\n"
        "📍 <b>Manzilimiz:</b> Toshkent shahri, Amir Temur ko'chasi, 15-uy\n"
        "📞 <b>Telefon:</b> +998 (90) 123-45-67\n"
        "🕒 <b>Ish vaqti:</b> Har kuni 09:00 dan 20:00 gacha\n\n"
        "Mavjud xizmatlarimiz va ustalar bilan tanishish yoki navbat olish uchun pastdagi menyudan foydalaning!"
    )
    bot.send_message(message.chat.id, about_text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "📅 Navbat olish") if bot else None
def handle_navbat_button(message):
    web_app_url = getattr(settings, 'MINI_APP_URL', 'http://127.0.0.1:8000/').strip()
    if web_app_url.startswith('https://'):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 Mini Appni ochish", web_app=types.WebAppInfo(url=web_app_url)))
        bot.send_message(message.chat.id, "Mini App orqali navbat olish uchun pastdagi tugmani bosing:", reply_markup=markup)
    else:
        text = (
            "📅 <b>Navbat olish (Mini App)</b>\n\n"
            "⚠️ Telegram Mini App ishlashi uchun <b>HTTPS</b> havolasi kerak.\n\n"
            "🛠 <i>Localhostda sinash uchun ngrok'dan foydalaning va settings.py fayliga https linkini kiriting.</i>\n\n"
            f"🌐 Brauzerda ochish uchun: {web_app_url}"
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['services']) if bot else None
@bot.message_handler(func=lambda m: m.text == "✂️ Xizmatlar") if bot else None
def show_services(message):
    services = Service.objects.all()
    if not services.exists():
        bot.send_message(message.chat.id, "Hozircha xizmatlar kiritilmagan.")
        return
        
    text = "✂️ <b>Bizning xizmatlar va narxlar:</b>\n\n"
    for s in services:
        name = html.escape(s.name)
        text += f"{s.icon} <b>{name}</b>\n"
        text += f"└ Narxi: {int(s.price):,} UZS | Davomiyligi: {s.duration_minutes} daqiqa\n\n"
        
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['barbers']) if bot else None
@bot.message_handler(func=lambda m: m.text == "👨🔧 Ustalar") if bot else None
def show_barbers(message):
    barbers = Barber.objects.all()
    if not barbers.exists():
        bot.send_message(message.chat.id, "Hozircha ustalar kiritilmagan.")
        return
        
    text = "👨🔧 <b>Bizning Royal ustalar:</b>\n\n"
    for b in barbers:
        stars = "⭐️" * int(b.rating)
        name = html.escape(b.name)
        spec = html.escape(b.specialty)
        text += f"👤 <b>{name}</b>\n"
        text += f"├ Mutaxassisligi: {spec}\n"
        text += f"└ Reytingi: {b.rating} {stars}\n\n"
        
    bot.send_message(message.chat.id, text, parse_mode="HTML")

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
        bot.send_message(message.chat.id, "Sizda faol navbatlar yo'q. Tugma orqali navbat oling! 📅")
        return
        
    bot.send_message(message.chat.id, "📋 <b>Sizning oxirgi navbatlaringiz:</b>", parse_mode="HTML")
    
    for b in bookings:
        status_emoji = {
            'pending': '⏳ Kutilmoqda',
            'confirmed': '✅ Tasdiqlandi',
            'cancelled': '❌ Bekor qilindi',
            'completed': '🎉 Yakunlandi'
        }.get(b.status, b.status)
        
        pay_status = "💳 To'langan" if b.is_paid else "⚠️ To'lanmagan"
        
        b_name = html.escape(b.barber.name)
        s_name = html.escape(b.service.name)
        
        zone_info = ""
        total_price = int(b.service.price)
        if b.zone:
            z_name = html.escape(b.zone.name)
            zone_info = f"🪑 Zona: <b>{z_name}</b>\n"
            total_price += int(b.zone.price)
            
        text = (
            f"📅 Sana: <b>{b.date}</b>\n"
            f"🕐 Vaqt: <b>{b.time_slot.strftime('%H:%M')}</b>\n"
            f"👨🔧 Usta: <b>{b_name}</b>\n"
            f"✂️ Xizmat: <b>{s_name}</b>\n"
            f"{zone_info}"
            f"Jami Narxi: {total_price:,} UZS\n"
            f"Holati: {status_emoji}\n"
            f"To'lov: {pay_status}"
        )
        
        markup = types.InlineKeyboardMarkup()
        if b.status in ['pending', 'confirmed']:
            btn_cancel = types.InlineKeyboardButton("❌ Navbatni bekor qilish", callback_data=f"cancel_{b.id}")
            markup.add(btn_cancel)
            if not b.is_paid:
                btn_pay = types.InlineKeyboardButton("💳 Hozir to'lash", callback_data=f"pay_{b.id}")
                markup.add(btn_pay)
                
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

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
        bot.send_message(message.chat.id, "Sizda to'lanishi kerak bo'lgan faol navbatlar yo'q. 😊")
        return
        
    for b in unpaid:
        b_name = html.escape(b.barber.name)
        s_name = html.escape(b.service.name)
        
        total_price = int(b.service.price)
        if b.zone:
            total_price += int(b.zone.price)
            
        text = (
            f"💳 <b>To'lov uchun navbat:</b>\n\n"
            f"Usta: {b_name}\n"
            f"Xizmat: {s_name}\n"
            f"Sana va Vaqt: {b.date} {b.time_slot.strftime('%H:%M')}\n"
            f"To'lov summasi: <b>{total_price:,} UZS</b>"
        )
        markup = types.InlineKeyboardMarkup()
        btn_pay = types.InlineKeyboardButton(f"To'lash ({total_price:,} UZS)", callback_data=f"pay_{b.id}")
        markup.add(btn_pay)
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
            f"❌ Ushbu navbat bekor qilindi:\n\nSana: {booking.date}\nUsta: {booking.barber.name}\nXizmat: {booking.service.name}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
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
        if provider_token:
            total_price = int(booking.service.price)
            if booking.zone:
                total_price += int(booking.zone.price)
                
            price_tiyin = total_price * 100 # In Telegram Payments, UZS smallest unit is tiyin (1 UZS = 100)
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
            bot.answer_callback_query(call.id, "To'lov muvaffaqiyatli qabul qilindi! ✅", show_alert=True)
            bot.edit_message_text(
                f"💳 To'lov muvaffaqiyatli amalga oshirildi!\n\nUsta: {booking.barber.name}\nXizmat: {booking.service.name}\nSana: {booking.date}\nHolat: ✅ To'landi",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
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
                f"🎉 <b>To'lov muvaffaqiyatli qabul qilindi! (Click)</b>\n\n"
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
        # 1. Webhook ni o'chiramiz
        bot.delete_webhook(drop_pending_updates=True)
        
        # 2. Eski polling ulanishini MAJBURAN uzamiz:
        #    get_updates chaqiruvi Telegram'da mavjud barcha eski
        #    getUpdates ulanishlarini darhol uzib tashlaydi.
        try:
            bot.get_updates(offset=-1, timeout=1)
            logger.info("Eski sessiya uzildi.")
        except Exception:
            pass
        
        _time.sleep(2)  # 2 soniya yetarli
        logger.info("Bot polling boshlanmoqda...")
        
        bot.infinity_polling(timeout=20, long_polling_timeout=20)
    else:
        logger.warning("Bot token not configured, skipping polling.")

if __name__ == '__main__':
    start_polling()
