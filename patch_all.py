import os

bot_path = 'barber/bot.py'
with open(bot_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix get_main_keyboard and handle_start
import re

content = re.sub(
    r'def get_main_keyboard\(\):.*?@bot\.message_handler\(commands=\[\'start\'\]\) if bot else None',
    '''def get_main_keyboard():
    # As requested by the user, we no longer use a reply keyboard. 
    # The 'Open' Menu Button is the primary way to interact.
    return types.ReplyKeyboardRemove()

@bot.message_handler(commands=['start']) if bot else None''',
    content, flags=re.DOTALL
)

content = re.sub(
    r'def handle_start\(message\):.*?bot\.send_message\(message\.chat\.id, welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard\(\)\)',
    '''def handle_start(message):
    try:
        tg_id = message.from_user.id
        first_name = message.from_user.first_name or "Mijoz"
        last_name = message.from_user.last_name or ""
        username = message.from_user.username or ""
        
        Customer.objects.get_or_create(
            telegram_id=tg_id,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'username': username
            }
        )
        
        welcome_text = (
            f"👋 Salom, <b>{first_name}</b>!\\n\\n"
            "💈 <b>Royal Barber</b> botiga xush kelibsiz.\\n\\n"
            "👇 Navbat olish yoki xizmatlarimizni ko'rish uchun chap pastki burchakdagi <b>«Open»</b> tugmasini bosing va ilovamizga kiring!"
        )
        
        bot.send_message(message.chat.id, welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Error in start command: {e}")''',
    content, flags=re.DOTALL
)

with open(bot_path, 'w', encoding='utf-8') as f:
    f.write(content)

html_path = 'barber/templates/barber/booking_app.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Greeting
html_content = html_content.replace(
    '<p class="subtitle" id="user-greeting">Xush kelibsiz!</p>',
    '<p class="subtitle" id="user-greeting"></p>'
)

# Input Field in Zone Selection
zone_input = """
    <!-- VIEW 1: Zone Selection -->
    <section class="view-section active" id="view-1">
        <div style="margin-bottom: 24px; text-align: left;">
            <label for="customer-name" style="font-size:14px; color:var(--hint-color); display:block; margin-bottom:8px;">Ismingiz:</label>
            <input type="text" id="customer-name" placeholder="Ismingizni kiriting" style="width: 100%; padding: 14px; border-radius: 12px; background: var(--secondary-bg-color); border: 1px solid var(--gold); color: var(--text-color); font-size: 16px; outline: none; transition: var(--transition);" />
        </div>
        <h2 class="section-title">🪑 Zonani tanlang</h2>
"""
html_content = html_content.replace(
    '<!-- VIEW 1: Zone Selection -->\n    <section class="view-section active" id="view-1">\n        <h2 class="section-title">🪑 Zonani tanlang</h2>',
    zone_input
)

# JS Updates
js_init = """
        tg.ready();
        tg.expand();
        
        const customerNameInput = document.getElementById('customer-name');
        if (tg.initDataUnsafe?.user) {
            document.getElementById('user-greeting').innerText = `Salom, hurmatli ${tg.initDataUnsafe.user.first_name}!`;
            customerNameInput.value = tg.initDataUnsafe.user.first_name;
        } else {
            document.getElementById('user-greeting').innerText = `Salom, hurmatli Mijoz!`;
            customerNameInput.value = '';
        }
        
        let selectedZone = null;
"""
html_content = html_content.replace(
    'tg.ready();\n        tg.expand();\n\n        let selectedZone = null;',
    js_init
)

html_content = html_content.replace(
    'if (currentStep === 1 && selectedZone !== null) isValid = true;',
    'if (currentStep === 1 && selectedZone !== null && customerNameInput.value.trim() !== "") isValid = true;'
)

payload_old = """            const payload = {
                tg_id: tg.initDataUnsafe?.user?.id || 123456789, // dummy for dev
                first_name: tg.initDataUnsafe?.user?.first_name || 'Test',"""
payload_new = """            const payload = {
                tg_id: tg.initDataUnsafe?.user?.id || 123456789, // dummy for dev
                first_name: customerNameInput.value.trim() || tg.initDataUnsafe?.user?.first_name || 'Mijoz',"""
html_content = html_content.replace(payload_old, payload_new)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Kiritish maydoni (Input) va bot o'zgarishlari muvaffaqiyatli saqlandi!")
