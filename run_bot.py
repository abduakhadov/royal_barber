import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from barber.bot import start_polling

if __name__ == '__main__':
    print("Bot ishga tushmoqda...")
    start_polling()
