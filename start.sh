#!/usr/bin/env bash
# Start script for Render.com

# 1. Telegram botni orqa fonda (background) ishga tushirish
echo "Starting Telegram Bot in background..."
python run_bot.py &

# 2. Django Gunicorn web serverni asosiy jarayonda ishga tushirish
echo "Starting Gunicorn Web Server..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
