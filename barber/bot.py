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

def get_main_menu():
    web_app_url = getattr(settings, 'MINI_APP_URL', 'http://127.0.0.1:8000/').strip()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Agar HTTPS bo'lsa Mini App tugmasi
    if web_app_url.startswith('https://'):
        btn_app = types.KeyboardButton("💈 Mini Appda bron qilish", web_app=types.WebAppInfo(url=web_app_url))
        markup.add(btn_app)
    else:
        btn_app = types.KeyboardButton("💈 Navbat olish")
        markup.add(btn_app)
        
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
                f"👋 Salom, <b>{first_name}</b>!\n\n"
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
        f"👋 Xush kelibsiz, <b>{first_name}</b>!\n\n"
        f"💈 <b>Professional ustalar, sifatli xizmat va qulay onlayn bron tizimi</b> — barchasi bir joyda.\n\n"
        f"✨ <i>O'zingizga qulay vaqtni tanlang va professional ustalarimiz xizmatidan bahramand bo'ling!</i>\n\n"
        f"👇 Quyidagi menyudan foydalaning yoki to'g'ridan-to'g'ri <b>Mini App</b>ni oching:"
    )
    
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    if web_app_url.startswith('https://'):
        inline_kb.add(types.InlineKeyboardButton("🚀 Mini Appda bron qilish", web_app=types.WebAppInfo(url=web_app_url)))
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
        "• /services — Bizning xizmatlar va narxlar\n"
        "• /barbers — Professional ustalar\n"
        "• /bookings — Sizning faol navbatlaringiz\n"
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
        "🕒 <b>Ish vaqti:</b> Har kuni 09:00 — 21:00\n\n"
        "✂️ Har bir xizmat yuqori sifat va e'tibor bilan bajariladi."
    )
    markup = types.InlineKeyboardMarkup()
    if website_url:
        markup.add(types.InlineKeyboardButton("🌐 Rasmiy sayt", url=website_url))
    if web_app_url.startswith('https://'):
        markup.add(types.InlineKeyboardButton("💈 Bron qilish", web_app=types.WebAppInfo(url=web_app_url)))
        
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

@bot.message_handler(func=lambda m: m.text in ["💈 Navbat olish", "💈 Mini Appda bron qilish"]) if bot else None
def handle_navbat_button(message):
    web_app_url = getattr(settings, 'MINI_APP_URL', 'https://royal-barber.onrender.com/').strip()
    markup = types.InlineKeyboardMarkup()
    if web_app_url.startswith('https://'):
        markup.add(types.InlineKeyboardButton("🚀 Mini Appni ochish", web_app=types.WebAppInfo(url=web_app_url)))
        bot.send_message(message.chat.id, "💈 <b>1 daqiqada onlayn navbat oling:</b>", parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f"🌐 Brauzerda ochish: {web_app_url}")


@bot.message_handler(commands=['services']) if bot else None
@bot.message_handler(func=lambda m: m.text == "✂️ Xizmatlar") if bot else None
def show_services(message):
    services = Service.objects.all()
    if not services.exists():
        bot.send_message(message.chat.id, "Hozircha xizmatlar kiritilmagan.")
        return
        
    web_app_url = getattr(settings, 'MINI_APP_URL', 'https://royal-barber.onrender.com/').strip()
    text = (
        "👑 <b>ROYAL BARBER | Xizmatlar</b>\n"
        "<i>Har bir xizmat yuqori sifat va e'tibor bilan bajariladi</i>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    for s in services:
        name = html.escape(s.name)
        text += f"✂️ <b>{name}</b>\n"
        text += f"💰 <b>{int(s.price):,} so'm</b>  |  ⏱ {s.duration_minutes} daqiqa\n"
        text += f"━━━━━━━━━━━━━━━━━━━━\n"
        
    markup = types.InlineKeyboardMarkup()
    if web_app_url.startswith('https://'):
        markup.add(types.InlineKeyboardButton("💈 Bron qilish", web_app=types.WebAppInfo(url=web_app_url)))
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

@bot.message_handler(commands=['barbers']) if bot else None
@bot.message_handler(func=lambda m: m.text == "👨‍🎨 Ustalar") if bot else None
def show_barbers(message):
    barbers = Barber.objects.all()
    if not barbers.exists():
        bot.send_message(message.chat.id, "Hozircha ustalar kiritilmagan.")
        return
        
    web_app_url = getattr(settings, 'MINI_APP_URL', 'https://royal-barber.onrender.com/').strip()
    text = (
        "👑 <b>ROYAL BARBER | Ustalarimiz</b>\n"
        "<i>Tajribali va professional sartaroshlar jamoasi</i>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    for b in barbers:
        name = html.escape(b.name)
        spec = html.escape(b.specialty or "Professional usta")
        rating = float(b.rating) if b.rating else 4.9
        stars = "⭐️" * int(round(rating))
        text += f"💈 <b>{name}</b>\n"
        text += f"👔 Tajriba / Mutaxassislik: {spec}\n"
        text += f"★ Reyting: <b>{rating:.2f}</b> {stars}\n"
        text += f"━━━━━━━━━━━━━━━━━━━━\n"
        
    markup = types.InlineKeyboardMarkup()
    if web_app_url.startswith('https://'):
        markup.add(types.InlineKeyboardButton("💈 Ustani tanlab bron qilish", web_app=types.WebAppInfo(url=web_app_url)))
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

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
