# SSL-BOT-for-telegram 🚀

![Главный скриншот](screenshots/screen1.jpg)

## О проекте
Telegram-бот для проверки SSL-сертификатов, работающий 24/7.  
Автоматическая проверка сайтов, логирование и уведомления.  

## 🚀 Возможности
- Автоматическая проверка SSL-сертификатов по URL
- Детальная информация: срок действия, издатель, PEM
- Поддержка кастомных портов
- Логирование с ротацией
- Обработка ошибок и таймаутов
  
## Технологии
- Python 3.10, asyncio
- Telegram Bot API
- CI/CD: GitHub Actions
- Raspberry Pi, systemd
- pytest, flake8, black

## 🏆 Ключевые достижения
- Сокращение времени проверки с 10 мин до 10 сек
- Предотвращение инцидентов с SSL
- 99.9% uptime, 1000+ запросов

## Скриншоты
![Скриншот 1](screenshots/Снимок экрана 2026-02-21 001718.jpg)

## Установка и запуск
``bash
git clone https://github.com/IOXNSUN/SSL-BOT-for-telegram.git
cd SSL-BOT-for-telegram
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python ssl_bot.py

CI/CD

Автоматическое тестирование через pytest
Автоматический деплой на Raspberry Pi через GitHub Actions
Telegram-уведомления о статусе тестов и деплоя

Ссылки
- 🚀 [Telegram-бот](https://t.me/CPA_SSL_BOT)
