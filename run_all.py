import subprocess
import sys
import os
import time

def run():
    print("=== Royal Barber Tizimi ===")

    # Start Django development server
    print("[1/2] Django serveri ishga tushirilmoqda...")
    django_proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"]
    )

    # Start Telegram bot polling
    print("[2/2] Telegram Bot ishga tushirilmoqda...")
    bot_proc = subprocess.Popen(
        [sys.executable, "run_bot.py"]
    )

    print("\n" + "="*40)
    print("  TIZIM ISHGA TUSHDI")
    print("  Web Server: http://127.0.0.1:8000")
    print("  Telegram Bot: Polling rejimida faol")
    print("="*40 + "\n")
    print("To'xtatish uchun Ctrl+C bosing.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTizim to'xtatilmoqda...")
    finally:
        django_proc.terminate()
        bot_proc.terminate()
        print("Xayr!")

if __name__ == '__main__':
    run()
