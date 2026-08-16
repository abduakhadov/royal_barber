import os
import sys
import subprocess
import threading
import time
import re
import signal

# Eski jarayonlarni tozalash
my_pid = os.getpid()
print(f"=== Royal Barber Avto-Tizimi (PID: {my_pid}) ===")
print("[*] Eski jarayonlar tozalanmoqda...")
subprocess.run(['taskkill', '/F', '/IM', 'cloudflared.exe', '/T'], 
               capture_output=True)
try:
    result = subprocess.run(
        ['wmic', 'process', 'where', 'name="python.exe"', 'get', 'processid,commandline'],
        capture_output=True, text=True, timeout=5
    )
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or 'ProcessId' in line:
            continue
        parts = line.rsplit(None, 1)
        if len(parts) == 2:
            try:
                pid = int(parts[1])
                if pid != my_pid and ('run_bot' in line or 'run_dev' in line or 'run_all' in line or 'manage.py' in line):
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
                    print(f"    [x] PID {pid} o'chirildi")
            except (ValueError, ProcessLookupError, PermissionError):
                pass
except Exception:
    pass
print("[+] Tozalash tugadi.\n")

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

CLOUDFLARED = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"

def load_token():
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('TELEGRAM_BOT_TOKEN='):
                return line.strip().split('=', 1)[1]
    return None

def update_env_url(new_url):
    if not new_url.endswith('/'):
        new_url += '/'
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with open('.env', 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith('MINI_APP_URL='):
                f.write(f'MINI_APP_URL={new_url}\n')
            else:
                f.write(line)
    print(f"[+] .env yangilandi: {new_url}")

def set_telegram_menu_button(url, token):
    if not token:
        return
    try:
        url_with_cache_bust = f"{url}?v={int(time.time())}"
        r = requests.post(
            f"https://api.telegram.org/bot{token}/setChatMenuButton",
            json={"menu_button": {"type": "web_app", "text": "Mini Ilova", "web_app": {"url": url_with_cache_bust}}},
            timeout=10
        )
        if r.json().get("ok"):
            print(f"[+] Telegram 'Mini Ilova' tugmasi yangilandi (URL: {url_with_cache_bust})")
    except Exception as e:
        print(f"[!] Telegram API: {e}")

def start_tunnel(token):
    """Tunnel ishga tushadi va URL topilganda .env va Telegram yangilanadi."""
    cf_exists = os.path.exists(CLOUDFLARED)
    
    if cf_exists:
        print("[*] Cloudflare tunnel ishga tushirilmoqda...")
        proc = subprocess.Popen(
            [CLOUDFLARED, 'tunnel', '--url', 'http://127.0.0.1:8000'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in iter(proc.stdout.readline, ''):
            match = re.search(r'(https://[a-zA-Z0-9\-]+\.trycloudflare\.com)', line)
            if match:
                url = match.group(1)
                print(f"[+] Tunnel: {url}")
                update_env_url(url)
                set_telegram_menu_button(url, token)
                break
        # Tunnelni tirik tutamiz
        proc.wait()
    else:
        print("[*] localhost.run tunnel urinilmoqda...")
        proc = subprocess.Popen(
            ['ssh', '-o', 'StrictHostKeyChecking=no', '-R', '80:localhost:8000', 'nokey@localhost.run'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in iter(proc.stdout.readline, ''):
            match = re.search(r'(https://[a-zA-Z0-9\-]+\.lhr\.life)', line)
            if match:
                url = match.group(1)
                print(f"[+] Tunnel: {url}")
                update_env_url(url)
                set_telegram_menu_button(url, token)
                break
        proc.wait()

if __name__ == '__main__':
    token = load_token()
    
    # 1. AVVAL Django serverni ishga tushiramiz
    print("[*] Django Server (port 8000) ishga tushirilmoqda...")
    server = subprocess.Popen([sys.executable, "manage.py", "runserver", "0.0.0.0:8000"])
    
    # Server to'liq tayyorlanishini kutamiz
    print("[*] Server tayyorlanmoqda...")
    time.sleep(5)
    
    # 2. Keyin tunnel ishga tushadi (arqa fonda)
    tunnel_thread = threading.Thread(target=start_tunnel, args=(token,), daemon=True)
    tunnel_thread.start()
    
    # 3. Bot ishga tushadi
    time.sleep(2)
    print("[*] Telegram Bot ishga tushirilmoqda...")
    bot_proc = subprocess.Popen([sys.executable, "run_bot.py"])
    
    print("\n========================================")
    print("  TIZIM ISHGA TUSHDI")
    print("  Lokal: http://127.0.0.1:8000/")
    print("  Tunnel URL tepada ko'rsatiladi")
    print("  To'xtatish: Ctrl+C")
    print("========================================\n")
    
    try:
        while True:
            bot_proc.wait()
            print("[!] Telegram Bot kutilmaganda to'xtadi! (409 Conflict yoki xato)")
            print("[*] 5 soniyadan so'ng qayta ishga tushiriladi...")
            time.sleep(5)
            bot_proc = subprocess.Popen([sys.executable, "run_bot.py"])
    except KeyboardInterrupt:
        print("\nXayr!")
        server.terminate()
        bot_proc.terminate()
        subprocess.run(['taskkill', '/F', '/IM', 'cloudflared.exe', '/T'], capture_output=True)
        sys.exit(0)
